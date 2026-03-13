from django.db import models
from django.conf import settings


class Profile(models.Model):
    """Extended profile for users (interviewer/employee and candidate). One-to-one with User."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True,
        max_length=255,
    )
    # Candidate-specific fields (optional)
    full_name = models.CharField(max_length=255, blank=True)
    professional_headline = models.CharField(max_length=255, blank=True)
    university = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
