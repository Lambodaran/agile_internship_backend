from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Profile
from .serializers import (
    ProfileSerializer,
    CandidateProfileSerializer,
    ChangePasswordSerializer,
)


def get_or_create_profile(user):
    """Get profile for user, creating one if it doesn't exist."""
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile_detail_update(request):
    """GET or update current user's interviewer profile (username, email, profile_photo)."""
    profile = get_or_create_profile(request.user)
    
    if request.method == 'GET':
        serializer = ProfileSerializer(profile, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # PUT / PATCH
    serializer = ProfileSerializer(
        profile, 
        data=request.data, 
        partial=(request.method == 'PATCH'),
        context={'request': request}  # Pass request to serializer context
    )
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def candidate_profile_detail_update(request):
    """GET or update current user's candidate profile (full_name, email, headline, university, location, photo)."""
    profile = get_or_create_profile(request.user)
    
    if request.method == 'GET':
        serializer = CandidateProfileSerializer(profile, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # For PUT/PATCH requests, ensure proper data parsing for multipart/form-data
    if request.method in ['PUT', 'PATCH']:
        # Handle file uploads properly
        data = request.data.dict() if hasattr(request.data, 'dict') else request.data
        
        serializer = CandidateProfileSerializer(
            profile, 
            data=data, 
            partial=(request.method == 'PATCH'),
            context={'request': request}  # Pass request to serializer context
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change password: current_password, new_password, confirm_new_password."""
    serializer = ChangePasswordSerializer(
        data=request.data, 
        context={'request': request}  # Pass request to serializer context
    )
    
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Password updated successfully."}, 
            status=status.HTTP_200_OK
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)