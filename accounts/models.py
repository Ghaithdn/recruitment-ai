from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('candidate', 'Candidat'),
        ('recruiter', 'Recruteur'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='candidate')
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_recruiter(self):
        return self.role == 'recruiter'

    def is_candidate(self):
        return self.role == 'candidate'

    def __str__(self):
        return f"{self.username} ({self.role})"