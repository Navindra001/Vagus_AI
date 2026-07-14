from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from .models import PatientCase
from .serializers import PatientCaseListSerializer, PatientCaseDetailSerializer


class CaseListView(ListAPIView):
    queryset = PatientCase.objects.filter(is_active=True)
    serializer_class = PatientCaseListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        specialty = self.request.query_params.get("specialty")
        difficulty = self.request.query_params.get("difficulty")
        if specialty:
            qs = qs.filter(specialty=specialty)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        return qs


class CaseDetailView(RetrieveAPIView):
    queryset = PatientCase.objects.filter(is_active=True)
    serializer_class = PatientCaseDetailSerializer
    permission_classes = [AllowAny]
