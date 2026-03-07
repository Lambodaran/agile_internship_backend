from rest_framework import generics, permissions
from internships.models import Internship
from internships.serializers import InternshipSerializer
from .permissions import IsEmployee,IsCandidate


# Create - only employee
class InternshipCreateView(generics.CreateAPIView):
    serializer_class = InternshipSerializer
    permission_classes = [IsEmployee]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

# List all
class InternshipListView(generics.ListAPIView):
    serializer_class = InternshipSerializer
    permission_classes = [IsEmployee]  # Restrict to employees

    def get_queryset(self):
        # Filter internships by the authenticated user
        return Internship.objects.filter(created_by=self.request.user).order_by('-created_at')

# Retrieve by ID
class InternshipDetailView(generics.RetrieveAPIView):
    queryset = Internship.objects.all()
    serializer_class = InternshipSerializer
    permission_classes = [permissions.IsAuthenticated]

# Update - only creator employee
class InternshipUpdateView(generics.UpdateAPIView):
    serializer_class = InternshipSerializer
    permission_classes = [IsEmployee]
    queryset = Internship.objects.all()

    def get_queryset(self):
        return Internship.objects.filter(created_by=self.request.user)

# Delete - only creator employee
class InternshipDeleteView(generics.DestroyAPIView):
    serializer_class = InternshipSerializer
    permission_classes = [IsEmployee]
    queryset = Internship.objects.all()

    def get_queryset(self):
        return Internship.objects.filter(created_by=self.request.user)

class AllInternshipsListView(generics.ListAPIView):
    serializer_class = InternshipSerializer
    permission_classes = [IsCandidate]  # Restrict to candidates
    queryset = Internship.objects.all().order_by('-created_at')


