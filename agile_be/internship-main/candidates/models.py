from django.db import models
from django.conf import settings
from internships.models import Internship
class CandidateProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='candidate_profile')
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    date_of_birth = models.DateField()
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    email = models.EmailField()
    contact_number = models.CharField(max_length=20)
    address = models.TextField()
    skills = models.CharField(max_length=300)  # Comma-separated or use ManyToMany if you prefer
    degrees = models.CharField(max_length=300)
    area_of_interest = models.CharField(max_length=120)
    graduation_year = models.CharField(max_length=20)
    college_name = models.CharField(max_length=120)
    department = models.CharField(max_length=120)
    passed_out_year = models.CharField(max_length=20)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True) # for file uploads

    def __str__(self):
        return self.user.username





class InternshipApplication(models.Model):
    INTERNSHIP_TYPE_CHOICES = [
        ('in_office', 'In-Office'),
        ('hybrid', 'Hybrid'),
        ('remote', 'Remote')
    ]

    FIELD_CHOICES = [
        ('accounts', 'Accounts'),
        ('administration', 'Administration'),
        ('chemical', 'Chemical'),
        ('technology', 'Technology'),
        ('finance', 'Finance'),
        ('banking', 'Banking'),
        ('healthcare', 'Healthcare'),
        ('human_resource', 'Human Resource'),
        ('education', 'Education'),
        ('engineering', 'Engineering'),
        ('retail', 'Retail'),
        ('marketing', 'Marketing'),
        ('hospitality', 'Hospitality'),
        ('consulting', 'Consulting'),
        ('manufacturing', 'Manufacturing'),
        ('media', 'Media'),
        ('transportation', 'Transportation'),
        ('telecommunications', 'Telecommunications'),
        ('nonprofit', 'Nonprofit'),
        ('activate_windows', 'Activate Windows')
    ]

    NATURE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
    ]

    DEGREE_CHOICES = [
        ('engineering', 'Engineering'),
        ('arts', 'Arts')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)  # Applicant
    company_name = models.CharField(max_length=255,null=True)
    internship_role = models.CharField(max_length=255,null=True)
    internship_type = models.CharField(max_length=20, choices=INTERNSHIP_TYPE_CHOICES,null=True)
    internship_field = models.CharField(max_length=50, choices=FIELD_CHOICES,null=True)
    internship_nature = models.CharField(max_length=20, choices=NATURE_CHOICES,null=True)
    internship_description = models.TextField(null=True)
    required_skills = models.CharField(max_length=255,null=True)
    duration_months = models.PositiveIntegerField(null=True)
    application_start_date = models.DateField(null=True)
    application_end_date = models.DateField(null=True)
    stipend = models.CharField(max_length=50,null=True)
    eligibility_criteria = models.TextField(null=True)
    degrees_preferred = models.CharField(max_length=100,null=True)
    contact_email = models.EmailField(null=True)
    contact_mobile_number = models.CharField(max_length=15,null=True)
    company_information = models.TextField(null=True)
    internship_responsibilities = models.TextField(null=True)
    total_vacancies = models.PositiveIntegerField(default=1)
    country = models.CharField(max_length=100,null=True)
    state = models.CharField(max_length=100,null=True)
    district = models.CharField(max_length=100,null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    resume = models.FileField(upload_to='resumes/')
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='applications',null=True, blank=True)
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending')
    #Candidate Details
    candidate_name = models.CharField(max_length=255, null=True, blank=True)
    candidate_email = models.EmailField(null=True, blank=True)
    candidate_phone = models.CharField(max_length=15, null=True, blank=True)
    
    
    test_score = models.FloatField(null=True, blank=True)
    test_passed = models.BooleanField(null=True, blank=True)
    test_completed = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.user.username} - {self.internship_role}" if self.user else f"{self.internship_role}"





class AssessmentResult(models.Model):
    candidate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assessment_results')
    internship_application = models.ForeignKey('InternshipApplication', on_delete=models.CASCADE, related_name='assessment_results')
    score = models.FloatField()
    passed = models.BooleanField()
    completed_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.candidate.username} - {self.internship_application.internship_role} - Score: {self.score}"
