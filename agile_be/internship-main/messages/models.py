from django.db import models
from django.conf import settings


class Message(models.Model):
    """Chat message between interviewer and candidate (for selected candidates only)."""

    SENDER_CHOICES = [
        ("interviewer", "Interviewer"),
        ("candidate", "Candidate"),
    ]

    application = models.ForeignKey(
        "candidates.InternshipApplication",
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )
    sender_type = models.CharField(max_length=20, choices=SENDER_CHOICES)
    sender_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_chat_messages",
    )
    content = models.TextField(blank=True)
    file = models.FileField(upload_to="message_attachments/", null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_type = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender_type} @ {self.created_at}"
