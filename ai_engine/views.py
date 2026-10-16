from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from jobs.models import Application
from .analyzer import analyze_application


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_cv(request, application_id):
    """
    Endpoint pour analyser une candidature.
    POST /api/ai/analyze/{application_id}/
    
    Déclenché automatiquement après chaque candidature
    OU manuellement par le recruteur.
    """
    try:
        # Récupère la candidature
        application = Application.objects.get(id=application_id)
    except Application.DoesNotExist:
        return Response(
            {"error": "Candidature introuvable."},
            status=status.HTTP_404_NOT_FOUND
        )

    # Lancer l'analyse IA
    score, skills = analyze_application(application)

    # Sauvegarder les résultats dans la DB
    application.match_score = score
    application.extracted_skills = skills
    application.save()

    return Response({
        "application_id": application_id,
        "match_score": score,
        "extracted_skills": skills,
        "message": f"Analyse terminée. Score: {score}%"
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_all_for_job(request, job_id):
    """
    Analyse TOUTES les candidatures d'une offre d'un coup.
    POST /api/ai/analyze-job/{job_id}/
    Utile pour le recruteur qui veut tout scorer en une fois.
    """
    applications = Application.objects.filter(
        job_offer__id=job_id,
        job_offer__recruiter=request.user
    )

    if not applications.exists():
        return Response({"error": "Aucune candidature trouvée."})

    results = []
    for app in applications:
        score, skills = analyze_application(app)
        app.match_score = score
        app.extracted_skills = skills
        app.save()
        results.append({
            "candidate": app.candidate.username,
            "score": score,
            "skills": skills
        })

    # Trier par score décroissant
    results.sort(key=lambda x: x["score"], reverse=True)

    return Response({
        "job_id": job_id,
        "total_analyzed": len(results),
        "results": results
    })