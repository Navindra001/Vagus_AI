from django.urls import path
from . import views

urlpatterns = [
    path("representative/chat/",   views.chat,          name="representative-chat"),
    path("representative/topics/", views.topic_summary, name="representative-topics"),
    path("debug/", debug_env),
]