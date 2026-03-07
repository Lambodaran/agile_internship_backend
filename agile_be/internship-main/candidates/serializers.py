from rest_framework import serializers
from .models import CandidateProfile
from .models import InternshipApplication
from internships.serializers import InternshipSerializer
class CandidateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateProfile
        fields = '__all__'
        read_only_fields = ['user']




class InternshipApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternshipApplication
        fields = '__all__'
        read_only_fields = ['user', 'applied_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional except user and applied_at (already read-only)
        for field_name, field in self.fields.items():
            if field_name not in self.Meta.read_only_fields:
                field.required = False
        
# serializers.py

class CandidateAcceptedApplicationSerializer(serializers.ModelSerializer):
    interview_id = serializers.SerializerMethodField()
    interview_date = serializers.SerializerMethodField()
    interview_time = serializers.SerializerMethodField()
    interview_zoom = serializers.SerializerMethodField()
    test_score = serializers.SerializerMethodField()
    class Meta:
        model = InternshipApplication
        fields = ['id', 'candidate_name', 'internship_role','test_score', 'interview_id', 'interview_date','interview_time','interview_zoom']

    def get_interview_id(self, obj):
        interview = obj.interviews.first()
        return interview.id if interview else None

    def get_interview_date(self, obj):
        interview = obj.interviews.first()
        return interview.date if interview else None
    
    def get_interview_time(self, obj):
       interview = obj.interviews.first()
       return interview.time.strftime('%H:%M') if interview and interview.time else None

    def get_interview_zoom(self, obj):
        interview = obj.interviews.first()
        return interview.zoom if interview else None
    
    def get_test_score(self, obj):
        if obj.test_score is not None:
            return round(obj.test_score, 2)
        return None

# class CandidateApplicationSerializer(serializers.ModelSerializer):
#     internship = serializers.SerializerMethodField()
#     test_scheduled = serializers.SerializerMethodField()
#     test_score = serializers.SerializerMethodField()
#     class Meta:
#         model = InternshipApplication
#         fields = [
#             'id',
#             'internship',
#             'company_name',
#             'internship_role',
#             'internship_type',
#             'internship_field',
#             'internship_nature',
#             'duration_months',
#             'applied_at',
#             'status',
#             'test_scheduled',
#             'test_score',
#             'test_passed',
#             'test_completed',
#         ]

#     def get_internship(self, obj):
#         internship = obj.internship
#         if internship:
#             return {
#                 'id': internship.id,
#                 'title': internship.internship_role,
#                 'company': internship.company_name,
#                 'location': f"{internship.district}, {internship.state}, {internship.country}",
#                 'duration': f"{internship.duration_months} Months",
#             }
#         return {
#             'id': None,
#             'title': obj.internship_role or 'N/A',
#             'company': obj.company_name or 'N/A',
#             'location': f"{obj.district or 'N/A'}, {obj.state or 'N/A'}, {obj.country or 'N/A'}",
#             'duration': f"{obj.duration_months or 'N/A'} Months",
#         }

#     def get_test_scheduled(self, obj):
#         internship = obj.internship
#         if internship and internship.quiz_set and obj.status == 'accepted':
#             return {
#                 'quiz_set_id': internship.quiz_set.id,
#                 'quiz_title': internship.quiz_set.title,
#                 'date': internship.quiz_open_date,
#                 'time': internship.quiz_open_time,
#                 'duration': internship.quiz_set.duration_minutes,
#                 'pass_percentage': internship.pass_percentage,
#             }
#         return None
    
#     def get_test_score(self, obj):
#         if obj.test_score is not None:
#             return round(obj.test_score, 2)  # <- round to 2 decimal places
#         return None




class CandidateApplicationSerializer(serializers.ModelSerializer):
    internship = InternshipSerializer(read_only=True)  # Nested live internship data
    test_scheduled = serializers.SerializerMethodField()
    test_score = serializers.SerializerMethodField()

    class Meta:
        model = InternshipApplication
        fields = [
            'id',
            'internship',          
            'applied_at',
            'status',
            'test_scheduled',
            'test_score',
            'test_passed',
            'test_completed',
        ]

    def get_test_scheduled(self, obj):
        internship = obj.internship
        if internship and getattr(internship, 'quiz_set', None) and obj.status == 'accepted':
            return {
                'quiz_set_id': internship.quiz_set.id,
                'quiz_title': internship.quiz_set.title,
                'date': internship.quiz_open_date,
                'time': internship.quiz_open_time,
                'duration': internship.quiz_set.duration_minutes,
                'pass_percentage': internship.pass_percentage,
            }
        return None

    def get_test_score(self, obj):
        if obj.test_score is not None:
            return round(obj.test_score, 2)
        return None
    
    
from .models import AssessmentResult

class AssessmentResultSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='internship_application.internship.company_name', read_only=True)
    internship_title = serializers.CharField(source='internship_application.internship.internship_role', read_only=True)
    completed_date = serializers.DateTimeField(format="%Y-%m-%d", read_only=True) 

    class Meta:
        model = AssessmentResult
        fields = [
            'id',
            'company_name',
            'internship_title',
            'score',
            'passed',
            'completed_date',
        ]