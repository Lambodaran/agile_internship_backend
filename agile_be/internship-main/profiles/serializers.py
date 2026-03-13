from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

# Max 5 MB for profile photo
MAX_PHOTO_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = ('image/png', 'image/jpeg', 'image/jpg', 'image/gif')


def validate_profile_photo(photo):
    if not photo:
        return
    if photo.size > MAX_PHOTO_SIZE:
        raise serializers.ValidationError(
            "Profile photo must be 5 MB or less."
        )
    content_type = getattr(photo, 'content_type', None) or getattr(photo, 'content_type', '')
    if content_type and content_type.lower() not in [t for t in ALLOWED_IMAGE_TYPES]:
        raise serializers.ValidationError(
            "Only PNG, JPG or GIF images are allowed."
        )


class ProfileSerializer(serializers.ModelSerializer):
    """Read/update current user profile: username, email, profile_photo."""
    username = serializers.CharField(source='user.username', max_length=150)
    email = serializers.EmailField(source='user.email', allow_blank=True)
    profile_photo = serializers.ImageField(required=False, allow_null=True)
    profile_photo_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'username', 'email', 'profile_photo', 'profile_photo_url']

    def get_profile_photo_url(self, obj):
        if obj.profile_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_photo.url)
            return obj.profile_photo.url
        return None

    def validate_username(self, value):
        user = self.context.get('request').user
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("This username is already in use.")
        return value

    def validate_email(self, value):
        user = self.context.get('request').user
        if value and User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate_profile_photo(self, value):
        validate_profile_photo(value)
        return value

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            for attr, val in user_data.items():
                setattr(instance.user, attr, val)
            instance.user.save()

        if 'profile_photo' in validated_data:
            instance.profile_photo = validated_data['profile_photo']
        instance.save()
        return instance


class CandidateProfileSerializer(serializers.ModelSerializer):
    """Read/update candidate profile: full_name, email, professional_headline, university, location, profile_photo."""
    email = serializers.EmailField(source='user.email', allow_blank=True)
    profile_photo = serializers.ImageField(required=False, allow_null=True)
    profile_photo_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'full_name', 'email', 'professional_headline',
            'university', 'location', 'profile_photo', 'profile_photo_url',
        ]

    def get_profile_photo_url(self, obj):
        if obj.profile_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_photo.url)
            return obj.profile_photo.url
        return None

    def validate_email(self, value):
        user = self.context.get('request').user
        if value and User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate_profile_photo(self, value):
        validate_profile_photo(value)
        return value

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            for attr, val in user_data.items():
                setattr(instance.user, attr, val)
            instance.user.save()
        if 'profile_photo' in validated_data:
            instance.profile_photo = validated_data['profile_photo']
        for attr in ('full_name', 'professional_headline', 'university', 'location'):
            if attr in validated_data:
                setattr(instance, attr, validated_data[attr])
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_new_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({
                "confirm_new_password": "New password and confirmation do not match."
            })
        user = self.context['request'].user
        if not user.check_password(data['current_password']):
            raise serializers.ValidationError({
                "current_password": "Current password is incorrect."
            })
        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
