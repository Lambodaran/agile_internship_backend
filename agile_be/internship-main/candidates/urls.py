from django.urls import path
from .views import CandidateProfileCreateView, CandidateProfileDetailView,ApplyInternshipView
from . import views


urlpatterns = [
    path('profile/create/', CandidateProfileCreateView.as_view(), name='candidate_profile_create'),
    path('profile/', CandidateProfileDetailView.as_view(), name='candidate_profile_detail_update'),
    
    path('apply-internship/', ApplyInternshipView.as_view(), name='apply_internship'),
    # path('candidate-applications/', views.candidate_applications, name='candidate-applications'),
    # path('interviewer-applications/', views.interviewer_applications, name='interviewer-applications'),
   path('application-counts/', views.candidate_application_counts, name='candidate-application-counts'),
   path('scheduled-interviews/', views.candidate_scheduled_interviews, name='candidate-scheduled-interviews'),
   path('list-applications/', views.list_candidate_applications, name='list_candidate_applications'),
    path('quiz/<int:quiz_id>/questions/', views.get_quiz_questions, name='get_quiz_questions'),
    path('submit-test-results/', views.submit_test_results, name='submit_test_results'),
    path('test-results/', views.test_results, name='test_results'),
    path('candidate_interview_calendar/', views.candidate_interview_calendar, name='candidate_interview_calendar'),
]

