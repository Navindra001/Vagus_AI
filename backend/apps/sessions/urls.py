from django.urls import path
from . import views

urlpatterns = [
    path("sessions/", views.create_session, name="session-create"),
    path("sessions/<uuid:session_id>/", views.get_session, name="session-detail"),
    path("sessions/<uuid:session_id>/chat/", views.chat, name="session-chat"),
    path("sessions/<uuid:session_id>/complete/", views.complete_session, name="session-complete"),
]
