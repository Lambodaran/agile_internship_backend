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
from notifications.services import create_quiz_completed_notification


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
        create_quiz_completed_notification(application)

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
    

from datetime import datetime
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def application_history(request):
    applications = (
        InternshipApplication.objects
        .filter(user=request.user)
        .select_related('internship')
        .prefetch_related('assessment_results', 'interviews')
        .order_by('-applied_at')
    )

    history_data = []

    for app in applications:
        timeline = []

        if app.internship:
            company = app.internship.company_name
            role = app.internship.internship_role
        else:
            company = getattr(app, 'company_name', None) or "Unknown Company"
            role = getattr(app, 'internship_role', None) or "Unknown Role"

        applied_ts = app.applied_at.isoformat() if app.applied_at else None

        # 1. Application Submitted
        if app.applied_at:
            timeline.append({
                "id": f"applied-{app.id}",
                "eventType": "applied",
                "title": "Application Submitted",
                "description": f"You applied for {role} at {company}.",
                "timestamp": applied_ts,
                "status": "completed",
            })

        # 2. Application Accepted
        if app.status == 'accepted':
            timeline.append({
                "id": f"application-accepted-{app.id}",
                "eventType": "application_accepted",
                "title": "Application Accepted",
                "description": "Your application was accepted. Please attend the scheduled quiz to move to the next stage.",
                "timestamp": applied_ts,
                "status": "completed",
            })

        assessment = app.assessment_results.order_by('completed_date').last()
        quiz_timestamp = None
        quiz_score = None

        # 3. Quiz Completed
        if assessment:
            quiz_timestamp = assessment.completed_date.isoformat() if assessment.completed_date else applied_ts
            quiz_score = round(assessment.score, 2) if assessment.score is not None else None

            title = f"Quiz Completed ({quiz_score}%)" if quiz_score is not None else "Quiz Completed"

            timeline.append({
                "id": f"quiz-{app.id}",
                "eventType": "quiz_completed",
                "title": title,
                "description": "Your assessment was submitted successfully.",
                "timestamp": quiz_timestamp,
                "status": "completed",
            })

        elif getattr(app, 'test_completed', False):
            quiz_timestamp = applied_ts
            quiz_score = round(app.test_score, 2) if app.test_score is not None else None

            title = f"Quiz Completed ({quiz_score}%)" if quiz_score is not None else "Quiz Completed"

            timeline.append({
                "id": f"quiz-{app.id}",
                "eventType": "quiz_completed",
                "title": title,
                "description": "Your assessment was submitted successfully.",
                "timestamp": quiz_timestamp,
                "status": "completed",
            })

        # 4. Shortlisted for Interview
        if getattr(app, 'test_passed', False):
            shortlist_timestamp = quiz_timestamp or applied_ts
            timeline.append({
                "id": f"shortlisted-{app.id}",
                "eventType": "shortlisted",
                "title": "Shortlisted for Interview",
                "description": "You passed the quiz and were shortlisted for the interview stage.",
                "timestamp": shortlist_timestamp,
                "status": "completed",
            })

        interview = app.interviews.order_by('date', 'time').first()

        if interview:
            interview_dt = None
            if interview.date:
                if interview.time:
                    interview_dt = datetime.combine(interview.date, interview.time)
                else:
                    interview_dt = datetime.combine(interview.date, datetime.min.time())

            interview_ts = interview_dt.isoformat() if interview_dt else applied_ts

            # 5. Interview Scheduled
            timeline.append({
                "id": f"interview-scheduled-{app.id}",
                "eventType": "interview_scheduled",
                "title": "Interview Scheduled",
                "description": f"Your interview for {role} was scheduled.",
                "timestamp": interview_ts,
                "status": "completed",
            })

            # 6. Interview Completed
            if interview.attended is True:
                timeline.append({
                    "id": f"interview-completed-{app.id}",
                    "eventType": "interview_completed",
                    "title": "Face-to-Face Interview Completed",
                    "description": "Your interview attendance was confirmed.",
                    "timestamp": interview_ts,
                    "status": "completed",
                })

            # 7. Final selection
            if interview.selected is True:
                timeline.append({
                    "id": f"selected-{app.id}",
                    "eventType": "offer_extended",
                    "title": "Selected for Internship",
                    "description": "You were selected after the interview.",
                    "timestamp": interview_ts,
                    "status": "completed",
                })
            elif interview.selected is False:
                timeline.append({
                    "id": f"not-selected-{app.id}",
                    "eventType": "rejected",
                    "title": "Not Selected After Interview",
                    "description": "You were not selected after the interview.",
                    "timestamp": interview_ts,
                    "status": "failed",
                })

        # Application-level rejection
        if app.status == 'rejected' and not any(item["eventType"] == "rejected" for item in timeline):
            timeline.append({
                "id": f"rejected-{app.id}",
                "eventType": "rejected",
                "title": "Application Rejected",
                "description": "Your application was not selected.",
                "timestamp": applied_ts,
                "status": "failed",
            })

        timeline.sort(key=lambda x: x["timestamp"] or "")

        current_status = "Application Submitted"
        final_outcome = None

        if app.status == 'rejected':
            current_status = "Rejected"
            final_outcome = "rejected"
        elif interview and interview.selected is True:
            current_status = "Selected for Internship"
            final_outcome = "accepted"
        elif interview and interview.selected is False:
            current_status = "Not Selected After Interview"
            final_outcome = "rejected"
        elif interview and interview.attended is True:
            current_status = "Interview Completed"
        elif interview:
            current_status = "Interview Scheduled"
        elif getattr(app, 'test_passed', False):
            current_status = "Shortlisted for Interview"
        elif getattr(app, 'test_completed', False):
            current_status = "Quiz Completed"
        elif app.status == 'accepted':
            current_status = "Application Accepted"

        history_data.append({
            "id": str(app.id),
            "company": company,
            "role": role,
            "appliedAt": applied_ts,
            "currentStatus": current_status,
            "finalOutcome": final_outcome,
            "timeline": timeline,
            "feedback": None,
        })

    return Response(history_data, status=200)

from .models import SavedInternship
from .serializers import SavedInternshipSerializer
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_saved_internships(request):
    saved_items = (
        SavedInternship.objects
        .filter(user=request.user)
        .select_related('internship')
        .order_by('-created_at')
    )
    serializer = SavedInternshipSerializer(saved_items, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_saved_internship(request):
    internship_id = request.data.get('internship_id')

    if not internship_id:
        return Response(
            {'error': 'internship_id is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    internship = get_object_or_404(Internship, id=internship_id)

    saved_item = SavedInternship.objects.filter(
        user=request.user,
        internship=internship
    ).first()

    if saved_item:
        saved_item.delete()
        return Response(
            {
                'saved': False,
                'message': 'Internship removed from saved list.'
            },
            status=status.HTTP_200_OK
        )

    SavedInternship.objects.create(
        user=request.user,
        internship=internship
    )
    return Response(
        {
            'saved': True,
            'message': 'Internship saved successfully.'
        },
        status=status.HTTP_201_CREATED
    )
    

from collections import Counter, defaultdict
from .models import InternshipApplication
from .serializers import SkillLeaderboardEntrySerializer


def normalize_field_label(value: str) -> str:
    if not value:
        return ""

    mapping = {
        "accounts": "Accounts",
        "administration": "Administration",
        "chemical": "Chemical",
        "technology": "Technology",
        "finance": "Finance",
        "banking": "Banking",
        "healthcare": "Healthcare",
        "human_resource": "Human Resource",
        "education": "Education",
        "engineering": "Engineering",
        "retail": "Retail",
        "marketing": "Marketing",
        "hospitality": "Hospitality",
        "consulting": "Consulting",
        "manufacturing": "Manufacturing",
        "media": "Media",
        "transportation": "Transportation",
        "telecommunications": "Telecommunications",
        "nonprofit": "Nonprofit",
        "activate_windows": "Activate Windows",
    }
    return mapping.get(value, value.replace("_", " ").title())


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def skill_leaderboard(request):
    applications = (
        InternshipApplication.objects.filter(
            test_completed=True,
            test_score__isnull=False,
            user__isnull=False,
        )
        .select_related("user", "internship")
        .order_by("-applied_at")
    )

    user_stats = defaultdict(
        lambda: {
            "user_id": None,
            "name": "",
            "username": None,
            "scores": [],
            "fields": [],
        }
    )

    for app in applications:
        user = app.user
        internship = app.internship

        internship_field = ""
        if internship and getattr(internship, "internship_field", None):
            internship_field = internship.internship_field
        elif getattr(app, "internship_field", None):
            internship_field = app.internship_field or ""

        field_label = normalize_field_label(internship_field)

        display_name = (
            (app.candidate_name or "").strip()
            or (user.get_full_name().strip() if hasattr(user, "get_full_name") else "")
            or getattr(user, "username", "")
            or "Candidate"
        )

        bucket = user_stats[user.id]
        bucket["user_id"] = user.id
        bucket["name"] = display_name
        bucket["username"] = getattr(user, "username", None)
        bucket["scores"].append(int(round(float(app.test_score or 0))))
        if field_label:
            bucket["fields"].append(field_label)

    leaderboard_rows = []

    for _, data in user_stats.items():
        scores = data["scores"]
        if not scores:
            continue

        avg_score = round(sum(scores) / len(scores))

        field_counter = Counter([f for f in data["fields"] if f])
        primary_field = field_counter.most_common(1)[0][0] if field_counter else ""

        leaderboard_rows.append(
            {
                "user_id": data["user_id"],
                "name": data["name"],
                "username": data["username"],
                "average_score": avg_score,
                "tests_completed": len(scores),
                "primary_field": primary_field,
            }
        )

    leaderboard_rows.sort(
        key=lambda x: (-x["average_score"], -x["tests_completed"], x["name"].lower())
    )

    total_participants = len(leaderboard_rows)

    ranked_rows = []
    for index, row in enumerate(leaderboard_rows, start=1):
        ranked_rows.append(
            {
                **row,
                "rank": index,
            }
        )

    current_user_payload = None
    for row in ranked_rows:
        if row["user_id"] == request.user.id:
            current_user_payload = {
                "user_id": row["user_id"],
                "name": row["name"],
                "username": row["username"],
                "rank": row["rank"],
                "average_score": row["average_score"],
                "tests_completed": row["tests_completed"],
            }
            break

    if current_user_payload is None:
        fallback_name = (
            request.user.get_full_name().strip()
            if hasattr(request.user, "get_full_name")
            else ""
        ) or getattr(request.user, "username", "Candidate")

        current_user_payload = {
            "user_id": request.user.id,
            "name": fallback_name,
            "username": getattr(request.user, "username", None),
            "rank": None,
            "average_score": 0,
            "tests_completed": 0,
        }

    top_score = ranked_rows[0]["average_score"] if ranked_rows else 0
    average_score = (
        round(sum(item["average_score"] for item in ranked_rows) / total_participants)
        if total_participants > 0
        else 0
    )

    field_values = ["All"]
    existing_fields = sorted(
        {item["primary_field"] for item in ranked_rows if item["primary_field"]}
    )
    field_values.extend(existing_fields)

    serialized_rows = SkillLeaderboardEntrySerializer(ranked_rows, many=True).data

    return Response(
        {
            "summary": {
                "total_participants": total_participants,
                "top_score": top_score,
                "average_score": average_score,
            },
            "current_user": current_user_payload,
            "filters": {
                "fields": field_values,
            },
            "leaderboard": serialized_rows,
        },
        status=status.HTTP_200_OK,
    )