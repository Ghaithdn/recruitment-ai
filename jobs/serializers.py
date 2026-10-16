from rest_framework import serializers
from .models import JobOffer, Application
from accounts.serializers import UserSerializer

class JobOfferSerializer(serializers.ModelSerializer):
    recruiter = UserSerializer(read_only=True)
    applications_count = serializers.SerializerMethodField()

    class Meta:
        model = JobOffer
        fields = ['id', 'recruiter', 'title', 'description', 'required_skills',
                  'location', 'contract_type', 'is_active', 'created_at', 'applications_count']
        read_only_fields = ['id', 'recruiter', 'created_at']

    def get_applications_count(self, obj):
        return obj.applications.count()


class ApplicationSerializer(serializers.ModelSerializer):
    candidate = UserSerializer(read_only=True)
    job_offer = JobOfferSerializer(read_only=True)
    job_offer_id = serializers.PrimaryKeyRelatedField(
        queryset=JobOffer.objects.all(), source='job_offer', write_only=True
    )

    class Meta:
        model = Application
        fields = ['id', 'candidate', 'job_offer', 'job_offer_id', 'cv',
                  'cover_letter', 'status', 'match_score', 'extracted_skills', 'applied_at']
        read_only_fields = ['id', 'candidate', 'status', 'match_score', 'extracted_skills', 'applied_at']

    def validate(self, attrs):
        request = self.context.get('request')
        job_offer = attrs.get('job_offer')
        if Application.objects.filter(candidate=request.user, job_offer=job_offer).exists():
            raise serializers.ValidationError("Vous avez déjà postulé à cette offre.")
        return attrs

    def validate_cv(self, value):
        if not value.name.endswith('.pdf'):
            raise serializers.ValidationError("Le CV doit être un fichier PDF.")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Le CV ne doit pas dépasser 5MB.")
        return value