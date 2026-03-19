from django.urls import path

from . import views


urlpatterns = [
    path("interviewer/notifications/", views.interviewer_notifications, name="interviewer-notifications"),
    path("candidate/notifications/", views.candidate_notifications, name="candidate-notifications"),
    path(
        "interviewer/notifications/<int:notification_id>/read/",
        views.mark_notification_read,
        name="mark-notification-read",
    ),
    path(
        "candidate/notifications/<int:notification_id>/read/",
        views.mark_notification_read,
        name="candidate-mark-notification-read",
    ),
    path(
        "interviewer/notifications/mark-all-read/",
        views.mark_all_notifications_read,
        name="mark-all-notifications-read",
    ),
    path(
        "candidate/notifications/mark-all-read/",
        views.mark_all_notifications_read,
        name="candidate-mark-all-notifications-read",
    ),
]
