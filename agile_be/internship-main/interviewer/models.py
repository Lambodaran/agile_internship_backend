from django.db import models
from candidates.models import InternshipApplication
# Create your models here.
class FaceToFaceInterview(models.Model):
    application = models.ForeignKey(InternshipApplication, on_delete=models.CASCADE, related_name='interviews')
    name = models.CharField(max_length=255)
    internship_role = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField(blank=True, null=True)
    zoom = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.internship_role} on {self.date}"