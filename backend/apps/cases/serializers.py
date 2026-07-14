from rest_framework import serializers
from .models import PatientCase


class PatientCaseListSerializer(serializers.ModelSerializer):
    """Lightweight — used in the case selection list."""
    class Meta:
        model  = PatientCase
        fields = ["id", "title", "patient_name", "age", "gender",
                  "condition", "specialty", "difficulty"]


class PatientCaseDetailSerializer(serializers.ModelSerializer):
    """Full detail — includes patient_story for the LLM prompt."""
    class Meta:
        model  = PatientCase
        fields = "__all__"
