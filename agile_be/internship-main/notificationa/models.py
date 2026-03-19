from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_NEW_MESSAGE = "new_message"
    TYPE_QUIZ_COMPLETED = "quiz_completed"
    TYPE_MEETING_ASAP = "meeting_asap"

    TYPE_CHOICES = [
        (TYPE_NEW_MESSAGE, "New Message"),
        (TYPE_QUIZ_COMPLETED, "Quiz Completed"),
        (TYPE_MEETING_ASAP, "Meeting ASAP"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    application = models.ForeignKey(
        "candidates.InternshipApplication",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    interview = models.ForeignKey(
        "interviewer.FaceToFaceInterview",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id} - {self.notification_type}"
