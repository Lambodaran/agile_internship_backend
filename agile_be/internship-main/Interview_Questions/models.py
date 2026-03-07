from django.db import models
from django.conf import settings

class Quiz(models.Model):
    title = models.CharField(max_length=255)
    # percentage_for_qualified = models.DecimalField(max_digits=5, decimal_places=2,null=True, blank=True)
    duration_minutes = models.IntegerField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()

class Option(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
