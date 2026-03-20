from django.shortcuts import render

# Create your views here.

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from internships.models import Internship
from interviewer.models import FaceToFaceInterview
from candidates.models import InternshipApplication
from candidates.serializers import InternshipApplicationSerializer,CandidateAcceptedApplicationSerializer
from rest_framework.permissions import IsAuthenticated


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def interviewer_dashboard_stats(request):
    user = request.user

    # Internships posted by this interviewer
    internships = Internship.objects.filter(created_by=user)
    total_jobs_posted = internships.count()

    # All applications to their internships
    applications = InternshipApplication.objects.filter(internship__in=internships)
    total_applications = applications.count()
    total_accepted = applications.filter(status='accepted').count()
    total_rejected = applications.filter(status='rejected').count()

    # Scheduled interviews by this interviewer
    interviews = FaceToFaceInterview.objects.filter(application__in=applications)

    interview_data = [
        {
            'id': interview.id,
            'candidate_name': interview.name,
            'internship_role': interview.internship_role,
            'date': interview.date,
            'time': interview.time.strftime('%I:%M %p') if interview.time else None,
            'zoom': interview.zoom,
            'company_name': interview.application.company_name if interview.application else None,
        }
        for interview in interviews
    ]

    return Response({
        'counts': {
            'total_jobs_posted': total_jobs_posted,
            'total_applications_received': total_applications,
            'total_accepted': total_accepted,
            'total_rejected': total_rejected,
        },
        'scheduled_interviews': interview_data,
    }, status=status.HTTP_200_OK)
   
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def interview_calendar(request):
    user = request.user
    internships = Internship.objects.filter(created_by=user)
    applications = InternshipApplication.objects.filter(internship__in=internships)
    interviews = FaceToFaceInterview.objects.filter(application__in=applications)

    interview_data = [
        {
            'id': interview.id,
            'candidate_name': interview.name,
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
    
    
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_internship_applications(request):
    internships = Internship.objects.filter(created_by=request.user)
    applications = InternshipApplication.objects.filter(internship__in=internships).order_by('-applied_at')
    serializer = InternshipApplicationSerializer(applications, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def list_accepted_applications(request):
#     internships = Internship.objects.filter(created_by=request.user)
#     accepted_applications = InternshipApplication.objects.filter(
#         internship__in=internships,
#         status='accepted'
#     ).order_by('-applied_at')

#     serializer = CandidateAcceptedApplicationSerializer(accepted_applications, many=True)
#     return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_passed_test_applications(request):
    internships = Internship.objects.filter(created_by=request.user)

    passed_test_applications = InternshipApplication.objects.filter(
        internship__in=internships,
        test_completed=True,     #Ensure test is completed
        test_passed=True         #Ensure test is passed
    ).order_by('-applied_at')

    serializer = CandidateAcceptedApplicationSerializer(passed_test_applications, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)





@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def edit_application(request, pk):
    try:
        application = InternshipApplication.objects.get(pk=pk, user=request.user)
    except InternshipApplication.DoesNotExist:
        return Response({"error": "Not found or unauthorized"}, status=status.HTTP_404_NOT_FOUND)

    serializer = InternshipApplicationSerializer(application, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_application(request, pk):
    try:
        application = InternshipApplication.objects.get(pk=pk, user=request.user)
    except InternshipApplication.DoesNotExist:
        return Response({"error": "Not found or unauthorized"}, status=status.HTTP_404_NOT_FOUND)

    application.delete()
    return Response({"message": "Deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


from rest_framework.views import APIView
class AcceptApplicationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            application = InternshipApplication.objects.get(pk=pk)
            application.status = 'accepted'
            application.save()
            return Response({'message': 'Application accepted successfully.'}, status=status.HTTP_200_OK)
        except InternshipApplication.DoesNotExist:
            return Response({'error': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)

class RejectApplicationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            application = InternshipApplication.objects.get(pk=pk)
            application.status = 'rejected'
            application.save()
            return Response({'message': 'Application rejected successfully.'}, status=status.HTTP_200_OK)
        except InternshipApplication.DoesNotExist:
            return Response({'error': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        
 

from interviewer.models import FaceToFaceInterview
from interviewer.serializers import PostInterviewDecisionSerializer
from messages.models import Message
from notifications.services import (
    create_asap_meeting_notification,
    create_candidate_asap_meeting_notification,
)
# from candidates.serializers import FaceToFaceInterviewSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_f2f(request):

    app_id = request.data.get("application_id")
    zoom = request.data.get("zoom")
    date = request.data.get("date")
    time = request.data.get("time")

    try:
        application = InternshipApplication.objects.get(id=app_id, status='accepted')

        # Prevent duplicate interview
        if FaceToFaceInterview.objects.filter(application=application).exists():
            return Response({'error': 'Face to face interview already scheduled for this candidate.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate Zoom URL
        validate = URLValidator()
        try:
            validate(zoom)
        except ValidationError:
            return Response({'error': 'Please enter a valid Zoom URL.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create interview
        interview = FaceToFaceInterview.objects.create(
            application=application,
            name=application.candidate_name,
            internship_role=application.internship_role,
            zoom=zoom,
            date=date,
            time=time 
        )
        create_asap_meeting_notification(interview)
        create_candidate_asap_meeting_notification(interview)

        return Response({'message': 'Interview scheduled successfully.'}, status=status.HTTP_201_CREATED)

    except InternshipApplication.DoesNotExist:
        return Response({'error': 'Application not found or not accepted.'}, status=status.HTTP_404_NOT_FOUND)







@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_f2f(request, pk):
    try:
        f2f = FaceToFaceInterview.objects.get(pk=pk)
        f2f.delete()
        return Response({'message': 'Interview deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

    except FaceToFaceInterview.DoesNotExist:
        return Response({'error': 'Interview record not found.'}, status=status.HTTP_404_NOT_FOUND)


from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_f2f(request, pk):
    try:
        f2f = FaceToFaceInterview.objects.get(pk=pk)

        zoom = request.data.get("zoom")
        date = request.data.get("date")
        time = request.data.get("time")

        # Validate and update Zoom URL
        if zoom is not None:
            validator = URLValidator()
            try:
                validator(zoom)
                f2f.zoom = zoom
            except ValidationError:
                return Response({'error': 'Invalid Zoom URL. It must start with http:// or https://'}, status=status.HTTP_400_BAD_REQUEST)

        # Update date directly (assuming frontend calendar ensures valid format)
        if date is not None:
            f2f.date = date
        if time is not None:
            f2f.time = time if time else None
        f2f.save()
        create_asap_meeting_notification(f2f)
        create_candidate_asap_meeting_notification(f2f)
        return Response({'message': 'Interview updated successfully.'}, status=status.HTTP_200_OK)

    except FaceToFaceInterview.DoesNotExist:
        return Response({'error': 'Interview record not found.'}, status=status.HTTP_404_NOT_FOUND)


# ─── Post-Interview Decisions (face-to-face only) ─────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def post_interview_decisions_list(request):
    """
    List candidates who have a scheduled face-to-face interview, for Post-Interview Decisions.
    Returns only face-to-face scheduled candidates with attended/selected fields.
    """
    user = request.user
    internships = Internship.objects.filter(created_by=user)
    applications = InternshipApplication.objects.filter(internship__in=internships)
    interviews = FaceToFaceInterview.objects.filter(application__in=applications).select_related('application').order_by('-date', '-time')
    serializer = PostInterviewDecisionSerializer(interviews, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_interview_status(request, pk):
    """
    Update attended and/or selected for a face-to-face interview (Post-Interview Decisions).
    Body: { "attended_meeting": true|false|null, "is_selected": true|false|null }
    """
    try:
        f2f = FaceToFaceInterview.objects.select_related('application', 'application__internship').get(pk=pk)
    except FaceToFaceInterview.DoesNotExist:
        return Response({'error': 'Interview not found.'}, status=status.HTTP_404_NOT_FOUND)
    if f2f.application.internship.created_by_id != request.user.id:
        return Response({'error': 'Not allowed to update this interview.'}, status=status.HTTP_403_FORBIDDEN)

    attended = request.data.get('attended_meeting')
    selected = request.data.get('is_selected')
    if attended is not None:
        f2f.attended = attended
    if selected is not None:
        f2f.selected = selected
    f2f.save()

    # When both Attended and Selected are True, send one automated congrats message (once per candidate)
    if f2f.attended and f2f.selected and not f2f.auto_congrats_sent:
        app = f2f.application
        score = app.test_score
        if score is not None:
            score_text = f" Your assessment score was {round(score)}%."
        else:
            score_text = ""
        congrats_content = (
            f"Congratulations, {f2f.name or 'you'}! "
            f"You have been selected for the {f2f.internship_role or 'this role'} position.{score_text} "
            "You can reply here if you have any questions."
        )
        Message.objects.create(
            application=app,
            sender_type='interviewer',
            sender_user=request.user,
            content=congrats_content,
        )
        f2f.auto_congrats_sent = True
        f2f.save(update_fields=['auto_congrats_sent'])

    serializer = PostInterviewDecisionSerializer(f2f)
    return Response(serializer.data, status=status.HTTP_200_OK)


def _get_date_range_start(date_range):
    if date_range == '7d':
        return timezone.now() - timedelta(days=7)
    if date_range == '30d':
        return timezone.now() - timedelta(days=30)
    if date_range == '90d':
        return timezone.now() - timedelta(days=90)
    if date_range == 'ytd':
        now = timezone.now()
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_analytics_pdf(request):
    """
    Download interviewer analytics report as PDF.
    Query params:
      - date_range: 7d|30d|90d|ytd|all
      - selected_role: internship role or all
    """
    user = request.user
    date_range = request.GET.get('date_range', '30d')
    selected_role = request.GET.get('selected_role', 'all')

    internships = Internship.objects.filter(created_by=user)
    if selected_role and selected_role != 'all':
        internships = internships.filter(internship_role=selected_role)

    applications = InternshipApplication.objects.filter(internship__in=internships).select_related('internship')
    start_date = _get_date_range_start(date_range)
    if start_date:
        applications = applications.filter(applied_at__gte=start_date)

    interviews = FaceToFaceInterview.objects.filter(application__in=applications).select_related('application')

    total_jobs = internships.count()
    total_applications = applications.count()
    total_accepted = applications.filter(status='accepted').count()
    total_rejected = applications.filter(status='rejected').count()
    took_quiz = applications.filter(test_completed=True).count()
    passed_quiz = applications.filter(test_passed=True).count()
    interviewed = interviews.count()
    hired = interviews.filter(selected=True).count()
    conversion_rate = round((total_accepted / total_applications) * 100, 2) if total_applications else 0

    role_summary = {}
    for app in applications:
        role = app.internship.internship_role if app.internship else 'Unknown'
        if role not in role_summary:
            role_summary[role] = {'total': 0, 'accepted': 0, 'rejected': 0}
        role_summary[role]['total'] += 1
        if app.status == 'accepted':
            role_summary[role]['accepted'] += 1
        if app.status == 'rejected':
            role_summary[role]['rejected'] += 1

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name='ReportTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=1,
        textColor=colors.HexColor('#0f172a'),
    )

    story = []
    story.append(Paragraph('Interviewer Analytics Report', title_style))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M')} | Date Range: {date_range.upper()} | Role: {selected_role}",
            styles['Normal'],
        )
    )
    story.append(Spacer(1, 14))

    summary_data = [
        ['Metric', 'Value'],
        ['Total Jobs Posted', str(total_jobs)],
        ['Total Applications', str(total_applications)],
        ['Total Accepted', str(total_accepted)],
        ['Total Rejected', str(total_rejected)],
        ['Quiz Attempted', str(took_quiz)],
        ['Quiz Passed', str(passed_quiz)],
        ['Interviews Scheduled', str(interviewed)],
        ['Hired (Selected)', str(hired)],
        ['Conversion Rate', f'{conversion_rate}%'],
    ]
    summary_table = Table(summary_data, colWidths=[260, 220])
    summary_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1d4ed8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.75, colors.HexColor('#cbd5e1')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph('Role-wise Applications', styles['Heading3']))
    role_table_data = [['Role', 'Total', 'Accepted', 'Rejected']]
    for role, values in role_summary.items():
        role_table_data.append(
            [role, str(values['total']), str(values['accepted']), str(values['rejected'])]
        )

    if len(role_table_data) == 1:
        role_table_data.append(['No data', '0', '0', '0'])

    role_table = Table(role_table_data, colWidths=[220, 85, 85, 90])
    role_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f766e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.75, colors.HexColor('#cbd5e1')),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]
        )
    )
    story.append(role_table)

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=interviewer_analytics_report.pdf'
    return response


from collections import defaultdict
from datetime import timedelta
from django.utils import timezone
from internships.models import Internship
from candidates.models import InternshipApplication
from interviewer.models import FaceToFaceInterview


def _get_date_range_start(date_range):
    if date_range == '7d':
        return timezone.now() - timedelta(days=7)
    if date_range == '30d':
        return timezone.now() - timedelta(days=30)
    if date_range == '90d':
        return timezone.now() - timedelta(days=90)
    if date_range == 'ytd':
        now = timezone.now()
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def interviewer_analytics_summary(request):
    user = request.user
    date_range = request.GET.get('date_range', '30d')
    selected_role = request.GET.get('selected_role', 'all')

    internships = Internship.objects.filter(created_by=user).order_by('-created_at')
    available_roles = list(
        internships.values_list('internship_role', flat=True).distinct()
    )

    if selected_role != 'all':
        internships = internships.filter(internship_role=selected_role)

    applications = InternshipApplication.objects.filter(
        internship__in=internships
    ).select_related('internship')

    start_date = _get_date_range_start(date_range)
    if start_date:
        applications = applications.filter(applied_at__gte=start_date)

    interviews = FaceToFaceInterview.objects.filter(
        application__in=applications
    ).select_related('application', 'application__internship')

    total_jobs_posted = internships.count()
    total_applications = applications.count()
    total_pending = applications.filter(status='pending').count()
    total_accepted = applications.filter(status='accepted').count()
    total_rejected = applications.filter(status='rejected').count()

    test_completed = applications.filter(test_completed=True).count()
    test_passed = applications.filter(test_passed=True).count()

    scheduled_interviews = interviews.count()
    attended_interviews = interviews.filter(attended=True).count()
    absent_interviews = interviews.filter(attended=False).count()
    selected_candidates = interviews.filter(selected=True).count()
    rejected_after_interview = interviews.filter(selected=False).count()
    pending_interview_decisions = interviews.filter(selected__isnull=True).count()

    role_breakdown_map = defaultdict(lambda: {
        "applications": 0,
        "completed_quiz": 0,
        "accepted": 0,
        "rejected": 0,
        "passed_quiz": 0,
        "selected": 0,
    })

    score_map = defaultdict(lambda: {"total": 0, "count": 0})

    for app in applications:
        role = app.internship.internship_role if app.internship else "Unknown"
        role_breakdown_map[role]["applications"] += 1

        if app.test_completed:
            role_breakdown_map[role]["completed_quiz"] += 1

        if app.status == "accepted":
            role_breakdown_map[role]["accepted"] += 1
        elif app.status == "rejected":
            role_breakdown_map[role]["rejected"] += 1

        if app.test_passed:
            role_breakdown_map[role]["passed_quiz"] += 1

        if app.test_score is not None:
            score_map[role]["total"] += float(app.test_score)
            score_map[role]["count"] += 1

    for interview in interviews:
        role = interview.internship_role or (
            interview.application.internship.internship_role
            if interview.application and interview.application.internship
            else "Unknown"
        )
        if interview.selected is True:
            role_breakdown_map[role]["selected"] += 1

    role_breakdown = []
    for role, values in role_breakdown_map.items():
        role_breakdown.append({
            "role": role,
            **values,
        })

    role_breakdown.sort(key=lambda x: x["applications"], reverse=True)

    avg_scores_by_role = []
    for role, values in score_map.items():
        avg_scores_by_role.append({
            "role": role,
            "average_score": round(values["total"] / values["count"], 2) if values["count"] else 0,
        })

    avg_scores_by_role.sort(key=lambda x: x["average_score"], reverse=True)

    return Response({
        "filters": {
            "date_range": date_range,
            "selected_role": selected_role,
            "available_roles": available_roles,
        },
        "overview": {
            "total_jobs_posted": total_jobs_posted,
            "total_applications": total_applications,
            "total_pending": total_pending,
            "total_accepted": total_accepted,
            "total_rejected": total_rejected,
            "test_completed": test_completed,
            "test_passed": test_passed,
            "scheduled_interviews": scheduled_interviews,
            "attended_interviews": attended_interviews,
            "absent_interviews": absent_interviews,
            "selected_candidates": selected_candidates,
            "rejected_after_interview": rejected_after_interview,
            "pending_interview_decisions": pending_interview_decisions,
        },
        "charts": {
            "application_status": [
                {"name": "Pending", "value": total_pending},
                {"name": "Accepted", "value": total_accepted},
                {"name": "Rejected", "value": total_rejected},
            ],
            "assessment_pipeline": [
                {"name": "Applications", "value": total_applications},
                {"name": "Quiz Completed", "value": test_completed},
                {"name": "Quiz Passed", "value": test_passed},
            ],
            "interview_outcomes": [
                {"name": "Scheduled", "value": scheduled_interviews},
                {"name": "Attended", "value": attended_interviews},
                {"name": "Absent", "value": absent_interviews},
                {"name": "Selected", "value": selected_candidates},
                {"name": "Not Selected", "value": rejected_after_interview},
                {"name": "Pending", "value": pending_interview_decisions},
            ],
            "role_breakdown": role_breakdown,
            "avg_scores_by_role": avg_scores_by_role,
        }
    })
    
    

from internships.models import Internship
from candidates.models import InternshipApplication
from interviewer.models import FaceToFaceInterview
from messages.models import Message

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def interviewer_talent_pool(request):
    user = request.user
    search = request.GET.get('search', '').strip().lower()
    selected_role = request.GET.get('role', 'all')
    selected_stage = request.GET.get('stage', 'all')

    internships = Internship.objects.filter(created_by=user)

    if selected_role != 'all':
        internships = internships.filter(internship_role=selected_role)

    applications = (
        InternshipApplication.objects
        .filter(internship__in=internships)
        .select_related('internship', 'user')
        .prefetch_related('interviews')
        .order_by('-applied_at')
    )

    candidates = []

    for app in applications:
        interview = app.interviews.order_by('-date', '-time').first()

        stage = 'applied'
        stage_label = 'Applied'

        if app.status == 'rejected':
            stage = 'rejected'
            stage_label = 'Rejected'
        elif interview and interview.selected is True:
            stage = 'selected'
            stage_label = 'Selected'
        elif interview and interview.attended is True:
            stage = 'interviewed'
            stage_label = 'Interview Attended'
        elif interview:
            stage = 'interview_scheduled'
            stage_label = 'Interview Scheduled'
        elif app.test_passed:
            stage = 'quiz_passed'
            stage_label = 'Quiz Passed'
        elif app.test_completed:
            stage = 'quiz_completed'
            stage_label = 'Quiz Completed'
        elif app.status == 'accepted':
            stage = 'accepted'
            stage_label = 'Application Accepted'

        company_name = (
            app.company_name or
            (app.internship.company_name if app.internship else '')
        )

        can_message = bool(interview and interview.attended is True and interview.selected is True)

        unread_count = 0
        if can_message:
            unread_count = Message.objects.filter(
                application=app,
                sender_type='candidate',
                read=False
            ).count()

        candidate = {
            "id": app.id,
            "candidate_name": app.candidate_name or "Candidate",
            "candidate_email": app.candidate_email or "",
            "candidate_phone": app.candidate_phone or "",
            "role": app.internship_role or (app.internship.internship_role if app.internship else ""),
            "company_name": company_name,
            "applied_at": app.applied_at.isoformat() if app.applied_at else None,
            "resume": app.resume.url if app.resume else None,
            "status": app.status,
            "test_score": round(app.test_score, 2) if app.test_score is not None else None,
            "test_completed": bool(app.test_completed),
            "test_passed": bool(app.test_passed),
            "stage": stage,
            "stage_label": stage_label,
            "interview_id": interview.id if interview else None,
            "interview_date": interview.date.isoformat() if interview and interview.date else None,
            "interview_time": interview.time.strftime('%H:%M') if interview and interview.time else None,
            "attended_meeting": interview.attended if interview else None,
            "is_selected": interview.selected if interview else None,
            "can_message": can_message,
            "unread_messages": unread_count,
        }

        searchable = " ".join([
            candidate["candidate_name"] or "",
            candidate["candidate_email"] or "",
            candidate["role"] or "",
            candidate["stage_label"] or "",
            candidate["company_name"] or "",
        ]).lower()

        if search and search not in searchable:
            continue

        if selected_stage != 'all' and candidate["stage"] != selected_stage:
            continue

        candidates.append(candidate)

    summary = {
        "total_candidates": len(candidates),
        "quiz_passed": sum(1 for c in candidates if c["test_passed"]),
        "interviews_scheduled": sum(1 for c in candidates if c["interview_id"]),
        "selected_candidates": sum(1 for c in candidates if c["is_selected"] is True),
        "average_score": round(
            sum(c["test_score"] for c in candidates if c["test_score"] is not None) /
            max(1, len([c for c in candidates if c["test_score"] is not None]))
        ) if any(c["test_score"] is not None for c in candidates) else 0,
    }

    available_roles = list(
        Internship.objects.filter(created_by=user)
        .values_list('internship_role', flat=True)
        .distinct()
    )

    return Response({
        "filters": {
            "roles": available_roles,
            "stages": [
                {"value": "all", "label": "All Stages"},
                {"value": "applied", "label": "Applied"},
                {"value": "accepted", "label": "Application Accepted"},
                {"value": "quiz_completed", "label": "Quiz Completed"},
                {"value": "quiz_passed", "label": "Quiz Passed"},
                {"value": "interview_scheduled", "label": "Interview Scheduled"},
                {"value": "interviewed", "label": "Interview Attended"},
                {"value": "selected", "label": "Selected"},
                {"value": "rejected", "label": "Rejected"},
            ]
        },
        "summary": summary,
        "results": candidates,
    })
    
