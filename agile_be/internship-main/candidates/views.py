from rest_framework import generics
from internships.models import  Internship
from candidates.serializers import CandidateProfileSerializer
from Interview_Questions.permissions import IsCandidate  # Add this import if IsCandidate is defined in permissions.py
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated






class CandidateProfileCreateView(generics.CreateAPIView):
    serializer_class = CandidateProfileSerializer
    permission_classes = [IsCandidate]
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CandidateProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = CandidateProfileSerializer
    permission_classes = [IsCandidate]
    def get_object(self):
        return self.request.user.candidate_profile


from .models import InternshipApplication
from .serializers import InternshipApplicationSerializer,CandidateAcceptedApplicationSerializer
from interviewer.models import FaceToFaceInterview
from django.shortcuts import get_object_or_404

class ApplyInternshipView(generics.CreateAPIView):
    serializer_class = InternshipApplicationSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        internship_id = request.data.get("internship")
        internship = get_object_or_404(Internship, id=internship_id)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, internship=internship)
            return Response({"message": "Application submitted successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def candidate_application_counts(request):
    user = request.user
    from django.db.models import Count, Q
    
    # Filter all applications by this user (candidate)
    queryset = InternshipApplication.objects.filter(user=user)
    
    counts = queryset.aggregate(
        applied=Count('id'),
        approved=Count('id', filter=Q(status='accepted')),
        rejected=Count('id', filter=Q(status='rejected'))
    )
    
    return Response(counts, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def candidate_scheduled_interviews(request):
    user = request.user

    # Get all applications of this user
    applications = InternshipApplication.objects.filter(user=user)

    # Get all interviews linked to those applications
    interviews = FaceToFaceInterview.objects.filter(application__in=applications)

    interview_data = [
        {
            'id': interview.id,
            'role': interview.internship_role,
            'date': interview.date,
            'time': interview.time,
            'zoom': interview.zoom,
            'company': interview.application.company_name if interview.application else None,
        }
        for interview in interviews
    ]

    return Response({
        'count': interviews.count(),
        'interviews': interview_data
    }, status=status.HTTP_200_OK)
    
    
from .models import InternshipApplication
from .serializers import CandidateApplicationSerializer
from Interview_Questions.models import Question, Quiz, Option
from Interview_Questions.serializers import QuestionSerializer


@api_view(['GET'])  
@permission_classes([IsAuthenticated])
def list_candidate_applications(request):
    applications = InternshipApplication.objects.filter(user=request.user).order_by('-applied_at')
    serializer = CandidateApplicationSerializer(applications, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quiz_questions(request, quiz_id):
    try:
        quiz = Quiz.objects.get(id=quiz_id)
        questions = quiz.questions.all()
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Quiz.DoesNotExist:
        return Response({'error': 'Quiz not found.'}, status=status.HTTP_404_NOT_FOUND)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_test_results(request):
    internship_id = request.data.get('internship_id')
    answers = request.data.get('answers')

    try:
        application = InternshipApplication.objects.get(id=internship_id, user=request.user)
        internship = application.internship
        quiz = internship.quiz_set

        correct_count = 0
        total_questions = quiz.questions.count()
        for question in quiz.questions.all():
            selected_option_index = answers.get(str(question.id))
            if selected_option_index is not None:
                try:
                    selected_option = question.options.all()[int(selected_option_index)]
                    if selected_option.is_correct:
                        correct_count += 1
                except (IndexError, ValueError):
                    continue

        score = round((correct_count / total_questions) * 100, 2) if total_questions > 0 else 0

        passed = score >= (internship.pass_percentage or 60)

        # Update InternshipApplication
        application.test_score = score
        application.test_passed = passed
        application.test_completed = True
        application.save()

        # Create AssessmentResult entry
        AssessmentResult.objects.create(
            candidate=request.user,
            internship_application=application,
            score=score,
            passed=passed,
            # completed_date will auto set by model's auto_now_add
        )

        return Response(
            {
                'score': score,
                'passed': passed,
                'test_completed': True,
                'test_score': score,
                'test_passed': passed,
                'message': 'Test results submitted successfully.',
            },
            status=status.HTTP_200_OK
        )
    except InternshipApplication.DoesNotExist:
        return Response({'error': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Quiz.DoesNotExist:
        return Response({'error': 'Quiz not found.'}, status=status.HTTP_404_NOT_FOUND)

    
    

from .models import AssessmentResult

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_results(request):
    try:
        user = request.user
        results = AssessmentResult.objects.filter(candidate=user).select_related('internship_application__internship')

        results_data = []
        passed_count = 0
        failed_count = 0
        total_score = 0
        valid_score_count = 0

        for res in results:
            score = res.score
            passed = res.passed

            if score > 0:
                total_score += score
                valid_score_count += 1

            if passed:
                passed_count += 1
            else:
                failed_count += 1

            results_data.append({
                'id': res.id,
                'company_name': res.internship_application.internship.company_name if res.internship_application.internship else 'Unknown Company',
                'internship_title': res.internship_application.internship.internship_role if res.internship_application.internship else 'Unknown Role',
                'score': round(score,2),
                'passed': passed,
                'completed_date': res.completed_date.isoformat(),
            })

        results_data.sort(key=lambda x: x['completed_date'], reverse=True)

        avg_score = round(total_score / valid_score_count) if valid_score_count > 0 else 0

        return Response({
            'results': results_data,
            'summary': {
                'passed_tests': passed_count,
                'failed_tests': failed_count,
                'average_score': avg_score,
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def candidate_interview_calendar(request):
    user = request.user
    
    # Get all applications of the logged-in candidate
    applications = InternshipApplication.objects.filter(user=user)
    
    # Get all interviews linked to those applications
    interviews = FaceToFaceInterview.objects.filter(application__in=applications)
    
    # Prepare interview data in similar format as interviewer calendar API
    interview_data = [
        {
            'id': interview.id,
            'internship_role': interview.internship_role,
            'date': interview.date.isoformat(),
            'time': interview.time.strftime('%I:%M %p') if interview.time else None,
            'zoom': interview.zoom,
            'company_name': interview.application.company_name if interview.application else None,
        }
        for interview in interviews
    ]
    
    return Response({
        'scheduled_interviews': interview_data,
    }, status=status.HTTP_200_OK)
