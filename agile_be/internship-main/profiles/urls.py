from django.urls import path
from . import views

urlpatterns = [
    path('', views.profile_detail_update, name='profile-detail-update'),
    path('candidate/', views.candidate_profile_detail_update, name='candidate-profile-detail-update'),
    path('change-password/', views.change_password, name='change-password'),
]
