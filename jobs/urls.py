from django.urls import path
from . import views

urlpatterns = [
    # Offres
    path('', views.JobOfferListView.as_view(), name='jobs-list'),
    path('create/', views.JobOfferCreateView.as_view(), name='jobs-create'),
    path('my/', views.MyJobOffersView.as_view(), name='my-jobs'),
    
    # Stats — Doit impérativement être avant <int:pk>/ pour éviter les conflits d'URL
    path('stats/', views.recruiter_stats, name='recruiter-stats'),
    
    path('<int:pk>/', views.JobOfferDetailView.as_view(), name='job-detail'),

    # Candidatures
    path('apply/', views.ApplyView.as_view(), name='apply'),
    path('my-applications/', views.MyApplicationsView.as_view(), name='my-applications'),
    path('<int:job_id>/applications/', views.JobApplicationsView.as_view(), name='job-applications'),
    path('applications/<int:pk>/status/', views.UpdateApplicationStatusView.as_view(), name='update-status'),
]