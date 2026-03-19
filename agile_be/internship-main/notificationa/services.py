from datetime import datetime, timedelta

from django.utils import timezone

from .models import Notification


def create_new_message_notification(application, candidate_name="Candidate"):
    internship = getattr(application, "internship", None)
    interviewer = getattr(internship, "created_by", None)
    if not interviewer:
        return None

    role_name = (
        getattr(application, "internship_role", "")
        or getattr(internship, "internship_role", "")
        or "role"
    )

    return Notification.objects.create(
        user=interviewer,
        application=application,
        notification_type=Notification.TYPE_NEW_MESSAGE,
        message=f"New message from {candidate_name} for {role_name}.",
    )


def create_quiz_completed_notification(application):
    internship = getattr(application, "internship", None)
    interviewer = getattr(internship, "created_by", None)
    if not interviewer:
        return None

    candidate_name = (
        (getattr(application, "candidate_name", "") or "").strip()
        or (getattr(application, "user", None).username if getattr(application, "user", None) else "Candidate")
    )
    role_name = (
        getattr(application, "internship_role", "")
        or getattr(internship, "internship_role", "")
        or "role"
    )

    obj, _ = Notification.objects.get_or_create(
        user=interviewer,
        application=application,
        notification_type=Notification.TYPE_QUIZ_COMPLETED,
        defaults={
            "message": f"{candidate_name} finished the quiz for {role_name}.",
        },
    )
    return obj


def create_asap_meeting_notification(interview):
    application = getattr(interview, "application", None)
    internship = getattr(application, "internship", None) if application else None
    interviewer = getattr(internship, "created_by", None) if internship else None
    if not interviewer:
        return None

    if not interview.date:
        return None

    meeting_time = interview.time or datetime.min.time()
    naive_dt = datetime.combine(interview.date, meeting_time)
    meeting_dt = timezone.make_aware(naive_dt) if timezone.is_naive(naive_dt) else naive_dt

    now = timezone.now()
    if not (now <= meeting_dt <= now + timedelta(hours=24)):
        return None

    candidate_name = (
        (getattr(interview, "name", "") or "").strip()
        or (getattr(application, "candidate_name", "") or "").strip()
        or "Candidate"
    )
    role_name = (
        getattr(interview, "internship_role", "")
        or getattr(application, "internship_role", "")
        or "role"
    )
    when_text = timezone.localtime(meeting_dt).strftime("%d %b %Y, %I:%M %p")

    obj, _ = Notification.objects.get_or_create(
        user=interviewer,
        interview=interview,
        notification_type=Notification.TYPE_MEETING_ASAP,
        defaults={
            "application": application,
            "message": f"Upcoming meeting with {candidate_name} for {role_name} at {when_text}.",
        },
    )
    return obj
