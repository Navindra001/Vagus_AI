from django.db import models
import uuid


class ConsultationSession(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("complete", "Complete"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        "apps_cases.PatientCase", on_delete=models.PROTECT, related_name="sessions"
    )
    user = models.ForeignKey(
        "apps_users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="sessions"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    messages = models.JSONField(default=list)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Session {self.id} - {self.case.title} ({self.status})"
