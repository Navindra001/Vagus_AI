from django.urls import path
from .views import get_feedback

urlpatterns = [
    path("feedback/<uuid:session_id>/", get_feedback, name="feedback"),
]
