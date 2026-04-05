from rest_framework import serializers
from notifications.models import Notification, UserNotification, Announcement, NotificationTemplate

class AdminUserNotificationSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    class Meta: model = UserNotification; fields = ["id", "user", "user_phone", "is_read", "read_at", "status", "error_message", "created_at"]

class AdminNotificationSerializer(serializers.ModelSerializer):
    recipients_count = serializers.SerializerMethodField(); recipients = AdminUserNotificationSerializer(source='user_notifications', many=True, read_only=True)
    class Meta: model = Notification; fields = ["id", "title", "body", "channel", "data", "recipients_count", "recipients", "created_at"]
    def get_recipients_count(self, obj): return obj.user_notifications.count()

class AdminAnnouncementSerializer(serializers.ModelSerializer):
    class Meta: model = Announcement; fields = '__all__'

class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta: model = NotificationTemplate; fields = ['id', 'slug', 'title', 'body', 'use_fcm', 'use_email', 'use_sms', 'use_whatsapp', 'is_active']

class AdminBulkSendNotificationSerializer(serializers.Serializer):
    recipient_type = serializers.ChoiceField(choices=[('all', 'All Users'), ('customers', 'All Customers'), ('agents', 'All Agents'), ('individuals', 'Specific Individuals')], default='individuals')
    user_ids, title, body, channels = serializers.ListField(child=serializers.IntegerField(), required=False), serializers.CharField(), serializers.CharField(), serializers.ListField(child=serializers.CharField()); data = serializers.JSONField(required=False, default={})
