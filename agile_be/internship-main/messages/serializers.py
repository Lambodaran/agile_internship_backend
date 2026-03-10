from rest_framework import serializers
from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender_type', read_only=True)
    timestamp = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'content', 'timestamp', 'read']

    def get_timestamp(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %I:%M %p') if obj.created_at else None
