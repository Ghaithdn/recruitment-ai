from django.urls import path
from . import views

urlpatterns = [
    path('analyze/<int:application_id>/', views.analyze_cv, name='analyze-cv'),
    path('analyze-job/<int:job_id>/', views.analyze_all_for_job, name='analyze-job'),
]