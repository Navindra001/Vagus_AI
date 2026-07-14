from django.db import models
import uuid


class PatientCase(models.Model):
    DIFFICULTY_CHOICES = [
        ("foundation", "Foundation"),
        ("core", "Core"),
        ("advanced", "Advanced"),
    ]

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title          = models.CharField(max_length=200)
    patient_name   = models.CharField(max_length=100)
    age            = models.PositiveSmallIntegerField()
    gender         = models.CharField(max_length=20)
    condition      = models.CharField(max_length=200)
    specialty      = models.CharField(max_length=100)
    difficulty     = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default="core")
    patient_story  = models.TextField(help_text="Full background story for the LLM system prompt")
    patient_role   = models.CharField(max_length=200, help_text="Personality descriptor, e.g. 'anxious but cooperative'")
    expected_diagnosis = models.CharField(max_length=200)
    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["specialty", "difficulty", "title"]

    def __str__(self):
        return f"{self.title} ({self.patient_name}, {self.age})"
