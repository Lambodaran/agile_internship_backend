from django.urls import path

from . import views


urlpatterns = [
    path("interviewer/notifications/", views.interviewer_notifications, name="interviewer-notifications"),
    path(
        "interviewer/notifications/<int:notification_id>/read/",
        views.mark_notification_read,
        name="mark-notification-read",
    ),
    path(
        "interviewer/notifications/mark-all-read/",
        views.mark_all_notifications_read,
        name="mark-all-notifications-read",
    ),
]
