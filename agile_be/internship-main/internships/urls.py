from django.urls import path
from .views import (
    InternshipCreateView, InternshipListView,
    InternshipDetailView, InternshipUpdateView, InternshipDeleteView,AllInternshipsListView
)
from . import views

urlpatterns = [
    path('list/', InternshipListView.as_view(), name='internship_list'),
    path('create/', InternshipCreateView.as_view(), name='internship_create'),
    path('<int:pk>/', InternshipDetailView.as_view(), name='internship_detail'),
    path('<int:pk>/edit/', InternshipUpdateView.as_view(), name='internship_edit'),
    path('<int:pk>/delete/', InternshipDeleteView.as_view(), name='internship_delete'),
     path('all-internships/', AllInternshipsListView.as_view(), name='all_internships_list'),
    
    

    
    
   
]
