from rest_framework import serializers
from notifications.models import UserNotification, Announcement

class UserNotificationSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='notification.title', read_only=True)
    body = serializers.CharField(source='notification.body', read_only=True)
    channel = serializers.CharField(source='notification.channel', read_only=True)
    data = serializers.JSONField(source='notification.data', read_only=True)
    class Meta:
        model = UserNotification
        fields = ['id', 'title', 'body', 'channel', 'data', 'is_read', 'read_at', 'created_at']
        read_only_fields = fields


class UserAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ['id', 'title', 'body', 'image', 'audience', 'starts_at', 'expires_at', 'created_at']
        read_only_fields = fields
