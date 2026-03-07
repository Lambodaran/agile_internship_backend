from django.urls import path
from .views import *
from . import views
urlpatterns = [
    path('create-quiz/', QuizCreateView.as_view(), name='create_quiz'),     # POST
    path('all-quiz/', QuizListView.as_view(), name='quiz_list'),     # GET all
    path('quiz/<int:pk>/', QuizDetailView.as_view(), name='quiz_detail'),  # GET by id
    path('<int:pk>/edit/', QuizUpdateView.as_view(), name='quiz_edit'),   # PUT/PATCH
    path('<int:pk>/delete/', QuizDeleteView.as_view(), name='quiz_delete'), # DELETE
    path('quiz-export/', ExportQuizExcelView.as_view(), name='quiz_export'),
    
    path('my-quiz/', MyQuizListView.as_view(), name='my_quizzes'),
    path('quiz-titles/', MyQuizTitlesView.as_view(), name='my_quiz_titles'),
    path('<int:quiz_id>/download-pdf/', views.download_quiz_pdf, name='download_quiz_pdf'),
]
