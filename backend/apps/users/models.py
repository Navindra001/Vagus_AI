from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extended user model — add VAGUS-specific fields here."""
    institution = models.CharField(max_length=200, blank=True)
    year_of_study = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "apps_users"

    def __str__(self):
        return self.username
