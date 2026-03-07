from rest_framework import serializers
from internships.models import Internship


class InternshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Internship
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at']




