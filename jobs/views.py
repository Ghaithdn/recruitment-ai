from django.db.models import Avg, Count, Q
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_engine.analyzer import analyze_application
from .models import JobOffer, Application
from .serializers import JobOfferSerializer, ApplicationSerializer


# ─── PERMISSIONS ──────────────────────────────────────────

class IsRecruiter(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'recruiter'

class IsCandidate(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'candidate'


# ─── JOB OFFERS ───────────────────────────────────────────

class JobOfferListView(generics.ListAPIView):
    """Tout le monde peut voir les offres actives"""
    serializer_class = JobOfferSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JobOffer.objects.filter(is_active=True)


class JobOfferCreateView(generics.CreateAPIView):
    """Seul le recruteur peut créer une offre"""
    serializer_class = JobOfferSerializer
    permission_classes = [IsRecruiter]

    def perform_create(self, serializer):
        serializer.save(recruiter=self.request.user)


class JobOfferDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Recruteur peut modifier/supprimer ses offres"""
    serializer_class = JobOfferSerializer
    permission_classes = [IsRecruiter]

    def get_queryset(self):
        return JobOffer.objects.filter(recruiter=self.request.user)


class MyJobOffersView(generics.ListAPIView):
    """Recruteur voit ses propres offres"""
    serializer_class = JobOfferSerializer
    permission_classes = [IsRecruiter]

    def get_queryset(self):
        return JobOffer.objects.filter(recruiter=self.request.user)


# ─── APPLICATIONS ─────────────────────────────────────────

class ApplyView(generics.CreateAPIView):
    """Candidat postule à une offre"""
    serializer_class = ApplicationSerializer
    permission_classes = [IsCandidate]

    def perform_create(self, serializer):
        application = serializer.save(candidate=self.request.user)
        try:
            score, skills = analyze_application(application)
            application.match_score = score
            application.extracted_skills = skills
            application.save()
            print(f"✅ IA: {application.candidate.username} → score {score}%")
        except Exception as e:
            print(f"⚠️ Erreur IA: {e}")


class MyApplicationsView(generics.ListAPIView):
    """Candidat voit ses candidatures"""
    serializer_class = ApplicationSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):
        return Application.objects.filter(candidate=self.request.user)


class JobApplicationsView(generics.ListAPIView):
    """Recruteur voit les candidatures pour une offre"""
    serializer_class = ApplicationSerializer
    permission_classes = [IsRecruiter]

    def get_queryset(self):
        job_id = self.kwargs['job_id']
        return Application.objects.filter(
            job_offer__id=job_id,
            job_offer__recruiter=self.request.user
        ).order_by('-match_score')


class UpdateApplicationStatusView(generics.UpdateAPIView):
    """Recruteur change le statut d'une candidature"""
    serializer_class = ApplicationSerializer
    permission_classes = [IsRecruiter]

    def get_queryset(self):
        return Application.objects.filter(job_offer__recruiter=self.request.user)

    def patch(self, request, *args, **kwargs):
        app = self.get_object()
        new_status = request.data.get('status')
        if new_status not in ['pending', 'reviewing', 'accepted', 'rejected']:
            return Response({'error': 'Statut invalide.'}, status=status.HTTP_400_BAD_REQUEST)
        app.status = new_status
        app.save()
        return Response(ApplicationSerializer(app).data)


# ─── STATS ENDPOINT ───────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsRecruiter])
def recruiter_stats(request):
    """
    Retourne toutes les statistiques du recruteur connecté.
    GET /api/jobs/stats/
    """
    # Toutes les offres du recruteur
    my_jobs = JobOffer.objects.filter(recruiter=request.user)
    
    # Toutes les candidatures pour ces offres
    all_apps = Application.objects.filter(job_offer__recruiter=request.user)
    
    # Stats de base
    total_offers = my_jobs.count()
    active_offers = my_jobs.filter(is_active=True).count()
    total_applications = all_apps.count()
    analyzed_applications = all_apps.filter(match_score__isnull=False).count()
    
    # Score moyen (seulement les candidatures analysées)
    avg_score = all_apps.filter(
        match_score__isnull=False
    ).aggregate(avg=Avg('match_score'))['avg']
    avg_score = round(avg_score, 1) if avg_score else 0
    
    # Distribution des scores par tranche
    score_distribution = [
        {
            "range": "0-20%",
            "count": all_apps.filter(match_score__gte=0, match_score__lt=20).count()
        },
        {
            "range": "20-40%",
            "count": all_apps.filter(match_score__gte=20, match_score__lt=40).count()
        },
        {
            "range": "40-60%",
            "count": all_apps.filter(match_score__gte=40, match_score__lt=60).count()
        },
        {
            "range": "60-80%",
            "count": all_apps.filter(match_score__gte=60, match_score__lt=80).count()
        },
        {
            "range": "80-100%",
            "count": all_apps.filter(match_score__gte=80, match_score__lte=100).count()
        },
    ]
    
    # Statuts des candidatures
    status_distribution = {
        "pending": all_apps.filter(status='pending').count(),
        "reviewing": all_apps.filter(status='reviewing').count(),
        "accepted": all_apps.filter(status='accepted').count(),
        "rejected": all_apps.filter(status='rejected').count(),
    }
    
    # Top 5 candidats par score
    top_candidates = all_apps.filter(
        match_score__isnull=False
    ).order_by('-match_score')[:5].values(
        'candidate__username',
        'candidate__email',
        'match_score',
        'job_offer__title',
        'status'
    )
    
    # Candidatures par offre
    apps_per_job = list(my_jobs.annotate(
        total=Count('applications')
    ).values('title', 'total').order_by('-total')[:5])
    
    return Response({
        "total_offers": total_offers,
        "active_offers": active_offers,
        "total_applications": total_applications,
        "analyzed_applications": analyzed_applications,
        "avg_score": avg_score,
        "score_distribution": score_distribution,
        "status_distribution": status_distribution,
        "top_candidates": list(top_candidates),
        "apps_per_job": apps_per_job,
    })