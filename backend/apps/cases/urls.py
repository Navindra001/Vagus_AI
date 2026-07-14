from django.urls import path
from .views import CaseListView, CaseDetailView

urlpatterns = [
    path("cases/", CaseListView.as_view(), name="case-list"),
    path("cases/<uuid:pk>/", CaseDetailView.as_view(), name="case-detail"),
]
