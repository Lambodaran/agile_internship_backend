from django.urls import path
from . import views
from . import views_candidate

urlpatterns = [
    # Interviewer side
    path("interviewer-conversations/", views.interviewer_conversations),
    path("conversations/<int:application_id>/messages/", views.conversation_messages),
    path("conversations/<int:application_id>/send/", views.send_message),

    # Candidate side
    path("candidate-conversations/", views_candidate.candidate_conversations),
    path(
        "candidate/conversations/<int:application_id>/messages/",
        views_candidate.candidate_conversation_messages,
    ),
    path(
        "candidate/conversations/<int:application_id>/send/",
        views_candidate.candidate_send_message,
    ),
]
