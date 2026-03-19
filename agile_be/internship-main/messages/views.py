from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import os

from internships.models import Internship
from candidates.models import InternshipApplication
from interviewer.models import FaceToFaceInterview
from .models import Message
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def interviewer_conversations(request):
    """
    List conversations for the Messages page: only candidates who have
    Attended = Yes AND Selected = Yes (face-to-face post-interview decisions).
    """
    user = request.user
    internships = Internship.objects.filter(created_by=user)
    applications = InternshipApplication.objects.filter(internship__in=internships)

    selected_interviews = FaceToFaceInterview.objects.filter(
        application__in=applications,
        attended=True,
        selected=True,
    ).select_related('application', 'application__internship', 'application__user').order_by('-date', '-time')

    conversations = []
    for f2f in selected_interviews:
        app = f2f.application
        internship = getattr(app, 'internship', None)
        company_name = app.company_name or (internship.company_name if internship else "")

        candidate_name = (
            (f2f.name or "").strip()
            or (app.candidate_name or "").strip()
            or (
                app.user.get_full_name().strip()
                if getattr(app, "user", None) and hasattr(app.user, "get_full_name")
                else ""
            )
            or (app.user.username if getattr(app, "user", None) else "")
            or 'Candidate'
        )

        last_msg = Message.objects.filter(application=app).order_by('-created_at').first()

        if last_msg:
            content = (last_msg.content or '').strip()

            if content:
                last_message = content
            elif last_msg.file:
                last_message = f"Attachment sent: {last_msg.file_name or 'File'}"
            else:
                last_message = 'No messages yet'
        else:
            last_message = 'No messages yet'

        last_message_time = (
            timezone.localtime(last_msg.created_at).isoformat() if last_msg else ''
        )

        unread_count = Message.objects.filter(
            application=app,
            sender_type='candidate',
            read=False
        ).count()

        conversations.append({
            'id': f'conv-{app.id}',
            'candidateName': candidate_name,
            'candidateId': str(app.user_id or app.id),
            'role': f2f.internship_role or app.internship_role or '',
            'companyName': company_name or 'Company',
            'lastMessage': last_message,
            'lastMessageTime': last_message_time,
            'unreadCount': unread_count,
            'starred': False,
            'applicationId': str(app.id),
            'messages': [],
        })

    return Response(conversations, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_messages(request, application_id):
    """
    Get all messages for a conversation (application).
    Only allowed for applications where candidate is attended + selected.
    """
    user = request.user
    try:
        app = InternshipApplication.objects.get(pk=application_id)
    except InternshipApplication.DoesNotExist:
        return Response({'error': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not app.internship or app.internship.created_by_id != user.id:
        return Response({'error': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)

    f2f = FaceToFaceInterview.objects.filter(
        application=app,
        attended=True,
        selected=True
    ).first()
    if not f2f:
        return Response(
            {'error': 'Candidate not in message list (not attended+selected).'},
            status=status.HTTP_403_FORBIDDEN
        )

    Message.objects.filter(
        application=app,
        sender_type='candidate',
        read=False
    ).update(read=True)

    messages = Message.objects.filter(application=app).order_by('created_at')

    data = []
    for m in messages:
        sender = 'recruiter' if m.sender_type == 'interviewer' else 'candidate'
        attachment = None

        if m.file:
            url = request.build_absolute_uri(m.file.url)
            name = m.file_name or os.path.basename(m.file.name)
            attachment = {
                'name': name,
                'url': url,
                'type': m.file_type or '',
            }

        data.append({
            'id': str(m.id),
            'sender': sender,
            'content': m.content,
            'timestamp': timezone.localtime(m.created_at).isoformat(),
            'read': m.read,
            'attachment': attachment,
        })

    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request, application_id):
    """
    Send a message in a conversation. Interviewer sends as 'interviewer'.
    """
    user = request.user
    try:
        app = InternshipApplication.objects.get(pk=application_id)
    except InternshipApplication.DoesNotExist:
        return Response({'error': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not app.internship or app.internship.created_by_id != user.id:
        return Response({'error': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)

    f2f = FaceToFaceInterview.objects.filter(application=app, attended=True, selected=True).first()
    if not f2f:
        return Response({'error': 'Candidate not in message list.'}, status=status.HTTP_403_FORBIDDEN)

    content = (request.data.get('content') or '').strip()
    uploaded_file = request.FILES.get('file')
    if not content and not uploaded_file:
        return Response({'error': 'Content or file is required.'}, status=status.HTTP_400_BAD_REQUEST)

    file_kwargs = {}
    if uploaded_file:
        file_kwargs['file'] = uploaded_file
        file_kwargs['file_name'] = uploaded_file.name
        file_kwargs['file_type'] = getattr(uploaded_file, 'content_type', '') or ''

    msg = Message.objects.create(
        application=app,
        sender_type='interviewer',
        sender_user=user,
        content=content,
        **file_kwargs,
    )
    attachment = None
    if msg.file:
        url = request.build_absolute_uri(msg.file.url)
        name = msg.file_name or os.path.basename(msg.file.name)
        attachment = {
            'name': name,
            'url': url,
            'type': msg.file_type or '',
        }
    return Response({
        'id': str(msg.id),
        'sender': 'recruiter',
        'content': msg.content,
        'timestamp': timezone.localtime(msg.created_at).isoformat(),
        'read': msg.read,
        'attachment': attachment,
    }, status=status.HTTP_201_CREATED)
