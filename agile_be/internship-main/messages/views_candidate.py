from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import os

from candidates.models import InternshipApplication
from interviewer.models import FaceToFaceInterview
from .models import Message

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def candidate_conversations(request):
    """List conversations for candidate: only their own applications with attended+selected F2F."""
    user = request.user
    applications = InternshipApplication.objects.filter(user=user)

    selected_interviews = (
        FaceToFaceInterview.objects.filter(
            application__in=applications,
            attended=True,
            selected=True,
        )
        .select_related("application", "application__internship")
        .order_by("-date", "-time")
    )

    conversations = []
    for f2f in selected_interviews:
        app = f2f.application
        internship = getattr(app, "internship", None)
        company_name = app.company_name or (internship.company_name if internship else "")
        role = f2f.internship_role or app.internship_role or ""
        recruiter = (
            internship.created_by.get_full_name()
            if internship and hasattr(internship.created_by, "get_full_name")
            else (internship.created_by.username if internship else "")
        )

        last_msg = Message.objects.filter(application=app).order_by("-created_at").first()
        last_message = last_msg.content if last_msg else "No messages yet"
        last_message_time = last_msg.created_at.strftime("%I:%M %p") if last_msg else ""
        if last_msg and (timezone.now() - last_msg.created_at).days >= 1:
            last_message_time = last_msg.created_at.strftime("%b %d")

        unread_count = Message.objects.filter(
            application=app,
            sender_type="interviewer",
            read=False
        ).count()

        conversations.append(
            {
                "id": f"conv-{app.id}",
                "companyName": company_name or "Company",
                "recruiterName": recruiter or "Interviewer",
                "role": role,
                "internshipId": str(internship.id) if internship else "",
                "applicationId": str(app.id),
                "lastMessage": last_message,
                "lastMessageTime": last_message_time,
                "unreadCount": unread_count,
                "messages": [],
            }
        )

    return Response(conversations, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def candidate_conversation_messages(request, application_id):
    """Messages for a candidate's conversation. Requires attended+selected F2F and ownership."""
    user = request.user

    try:
        app = InternshipApplication.objects.get(pk=application_id, user=user)
    except InternshipApplication.DoesNotExist:
        return Response({"error": "Application not found."}, status=status.HTTP_404_NOT_FOUND)

    f2f = FaceToFaceInterview.objects.filter(
        application=app,
        attended=True,
        selected=True
    ).first()

    if not f2f:
        return Response(
            {"error": "Conversation not available."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Mark recruiter messages as read when candidate opens the chat
    Message.objects.filter(
        application=app,
        sender_type="interviewer",
        read=False
    ).update(read=True)

    messages = Message.objects.filter(application=app).order_by("created_at")

    data = []

    for m in messages:
        if m.sender_type == "interviewer":
            sender = "recruiter"
        elif m.sender_type == "candidate":
            sender = "candidate"
        else:
            sender = "system"

        attachment = None
        if m.file:
            url = request.build_absolute_uri(m.file.url)
            name = m.file_name or os.path.basename(m.file.name)

            attachment = {
                "name": name,
                "url": url,
                "type": m.file_type or "",
            }

        data.append(
            {
                "id": str(m.id),
                "sender": sender,
                "content": m.content,
                "timestamp": m.created_at.strftime("%b %d %I:%M %p"),
                "read": m.read,
                "attachment": attachment,
            }
        )

    return Response(data, status=status.HTTP_200_OK)




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def candidate_send_message(request, application_id):
    """Candidate sends a message in their conversation."""
    user = request.user
    try:
        app = InternshipApplication.objects.get(pk=application_id, user=user)
    except InternshipApplication.DoesNotExist:
        return Response({"error": "Application not found."}, status=status.HTTP_404_NOT_FOUND)

    f2f = FaceToFaceInterview.objects.filter(
        application=app, attended=True, selected=True
    ).first()
    if not f2f:
        return Response(
            {"error": "Conversation not available."},
            status=status.HTTP_403_FORBIDDEN,
        )

    content = (request.data.get("content") or "").strip()
    uploaded_file = request.FILES.get("file")
    if not content and not uploaded_file:
        return Response({"error": "Content or file is required."}, status=status.HTTP_400_BAD_REQUEST)

    file_kwargs = {}
    if uploaded_file:
        file_kwargs["file"] = uploaded_file
        file_kwargs["file_name"] = uploaded_file.name
        file_kwargs["file_type"] = getattr(uploaded_file, "content_type", "") or ""

    msg = Message.objects.create(
        application=app,
        sender_type="candidate",
        sender_user=user,
        content=content,
        **file_kwargs,
    )
    attachment = None
    if msg.file:
        url = request.build_absolute_uri(msg.file.url)
        name = msg.file_name or os.path.basename(msg.file.name)
        attachment = {
            "name": name,
            "url": url,
            "type": msg.file_type or "",
        }
    return Response(
        {
            "id": str(msg.id),
            "sender": "candidate",
            "content": msg.content,
            "timestamp": msg.created_at.strftime("%b %d %I:%M %p"),
            "read": msg.read,
            "attachment": attachment,
        },
        status=status.HTTP_201_CREATED,
    )

