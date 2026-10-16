from django.db import models
from accounts.models import User

class JobOffer(models.Model):
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_offers')
    title = models.CharField(max_length=200)
    description = models.TextField()
    required_skills = models.JSONField(default=list)
    location = models.CharField(max_length=100, blank=True)
    contract_type = models.CharField(max_length=50, choices=[
        ('cdi', 'CDI'), ('cdd', 'CDD'), ('stage', 'Stage'), ('freelance', 'Freelance')
    ], default='cdi')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} — {self.recruiter.username}"

    class Meta:
        ordering = ['-created_at']


class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('reviewing', 'En cours d\'examen'),
        ('accepted', 'Retenu'),
        ('rejected', 'Refusé'),
    ]
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    job_offer = models.ForeignKey(JobOffer, on_delete=models.CASCADE, related_name='applications')
    cv = models.FileField(upload_to='cvs/')
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    match_score = models.FloatField(null=True, blank=True)
    extracted_skills = models.JSONField(default=list)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.candidate.username} → {self.job_offer.title}"

    class Meta:
        ordering = ['-match_score', '-applied_at']
        unique_together = ['candidate', 'job_offer']