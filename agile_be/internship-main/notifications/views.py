from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from candidates.models import InternshipApplication
from interviewer.models import FaceToFaceInterview

from .models import Notification
from .services import (
    create_asap_meeting_notification,
    create_candidate_asap_meeting_notification,
    create_candidate_asap_test_schedule_notification,
)


def _get_action_path(notification, user):
    if notification.notification_type == Notification.TYPE_NEW_MESSAGE:
        return "/candidate-messages" if getattr(user, "role", "") == "candidate" else "/interviewer-messages"
    if notification.notification_type == Notification.TYPE_QUIZ_COMPLETED:
        return "/interviewer-f2f"
    if notification.notification_type == Notification.TYPE_MEETING_ASAP:
        return "/candidate-calendar" if getattr(user, "role", "") == "candidate" else "/interviewer-calendar"
    if notification.notification_type == Notification.TYPE_TEST_SCHEDULE_ASAP:
        return "/applied-internship"
    return "/candidate-dashboard" if getattr(user, "role", "") == "candidate" else "/interviewer-dashboard"


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def interviewer_notifications(request):
    internships = request.user.internships.all()
    applications = InternshipApplication.objects.filter(internship__in=internships)
    interviews = FaceToFaceInterview.objects.filter(application__in=applications)

    # Build dynamic ASAP meeting alerts (same idea as dashboard alert aggregation).
    for interview in interviews:
        create_asap_meeting_notification(interview)

    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    data = [
        {
            "id": n.id,
            "type": n.notification_type,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
            "application_id": n.application_id,
            "interview_id": n.interview_id,
            "action_path": _get_action_path(n, request.user),
        }
        for n in notifications
    ]

    unread_count = notifications.filter(is_read=False).count()
    return Response(
        {
            "unread_count": unread_count,
            "notifications": data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def candidate_notifications(request):
    applications = InternshipApplication.objects.filter(user=request.user).select_related("internship")
    interviews = FaceToFaceInterview.objects.filter(application__in=applications)

    for interview in interviews:
        create_candidate_asap_meeting_notification(interview)

    for application in applications:
        create_candidate_asap_test_schedule_notification(application)

    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    data = [
        {
            "id": n.id,
            "type": n.notification_type,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
            "application_id": n.application_id,
            "interview_id": n.interview_id,
            "action_path": _get_action_path(n, request.user),
        }
        for n in notifications
    ]

    unread_count = notifications.filter(is_read=False).count()
    return Response(
        {
            "unread_count": unread_count,
            "notifications": data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
    except Notification.DoesNotExist:
        return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)

    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return Response({"message": "Notification marked as read."}, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({"message": "All notifications marked as read."}, status=status.HTTP_200_OK)
