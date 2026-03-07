from django.urls import path
from .views import AcceptApplicationView, RejectApplicationView
from . import views


urlpatterns = [
   
   path('interviewer-dashboard/', views.interviewer_dashboard_stats, name='interviewer-dashboard'),
   path('interview_calendar/', views.interview_calendar, name='interview_calendar'),
   path('applications/', views.list_internship_applications, name='list-internship-applications'),
   path('applications/<int:pk>/edit/', views.edit_application, name='edit-application'),
   path('applications/<int:pk>/delete/', views.delete_application, name='delete-application'),
   path('applications/<int:pk>/accept/', AcceptApplicationView.as_view(), name='accept-application'),
   path('applications/<int:pk>/reject/', RejectApplicationView.as_view(), name='reject-application'),
   path('passed-candidates/', views.list_passed_test_applications, name='list-passed-test-applications'),
   path('interview/create/', views.create_f2f, name='create-f2f'),
   path('interview/update/<int:pk>/', views.update_f2f, name='update-f2f'),
   path('interview/delete/<int:pk>/', views.delete_f2f, name='delete-f2f'),
]

