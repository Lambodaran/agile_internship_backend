
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
    
