
from rest_framework import serializers

from interviewer.models import FaceToFaceInterview




class FaceToFaceInterviewSerializer(serializers.ModelSerializer):
    company = serializers.CharField(source='application.company_name', read_only=True)
    time = serializers.SerializerMethodField()
    class Meta:
        model = FaceToFaceInterview
        fields = ['id', 'name', 'internship_role', 'date', 'zoom', 'company','time']
        
    def get_time(self, obj):
        if obj.time:
            # Format time as HH:MM AM/PM
            return obj.time.strftime('%I:%M %p')  
        return None


class PostInterviewDecisionSerializer(serializers.ModelSerializer):
    """Serializer for Post-Interview Decisions: face-to-face scheduled candidates with attended/selected."""
    id = serializers.IntegerField(source='application.id', read_only=True)
    candidate_name = serializers.CharField(source='name', read_only=True)
    internship_role = serializers.CharField(read_only=True)
    test_score = serializers.SerializerMethodField()
    interview_id = serializers.IntegerField(source='id', read_only=True)
    interview_date = serializers.DateField(source='date', format='%Y-%m-%d')
    interview_time = serializers.SerializerMethodField()
    attended_meeting = serializers.BooleanField(source='attended', allow_null=True)
    is_selected = serializers.BooleanField(source='selected', allow_null=True)

    class Meta:
        model = FaceToFaceInterview
        fields = [
            'id', 'candidate_name', 'internship_role', 'test_score',
            'interview_id', 'interview_date', 'interview_time',
            'attended_meeting', 'is_selected',
        ]

    def get_test_score(self, obj):
        if obj.application and obj.application.test_score is not None:
            return round(obj.application.test_score, 2)
        return None

    def get_interview_time(self, obj):
        if obj.time:
            return obj.time.strftime('%H:%M')
        return None

