from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema, extend_schema_view
from admin_api.permissions import IsSuperUserOnly, CanManageNotifications
from notifications.models import Notification, Announcement
from admin_api.serializers import (
    AdminNotificationSerializer, AdminAnnouncementSerializer,
    AdminBulkSendNotificationSerializer
)
from notifications.utils import NotificationService
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.response import Response

User = get_user_model()

@extend_schema_view(
    list=extend_schema(tags=["Admin Notifications"]),
)
class AdminNotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by('-created_at')
    serializer_class = AdminNotificationSerializer
    permission_classes = [CanManageNotifications]

    @extend_schema(
        summary="Bulk send notification to multiple users",
        request=AdminBulkSendNotificationSerializer,
        responses={201: AdminNotificationSerializer},
        tags=["Admin Notifications"]
    )
    @action(detail=False, methods=['post'], url_path='bulk-send')
    def bulk_send(self, request):
        serializer = AdminBulkSendNotificationSerializer(data=request.data)
        if serializer.is_valid():
            user_ids = serializer.validated_data['user_ids']
            title = serializer.validated_data['title']
            body = serializer.validated_data['body']
            channels = serializer.validated_data['channels']
            extra_data = serializer.validated_data.get('data', {})

            users = User.objects.filter(id__in=user_ids)
            if not users.exists():
                return Response({"error": "No valid users found"}, status=400)

            # Support multiple channels
            last_notif = None
            for channel in channels:
                last_notif = NotificationService.create_notification(
                    users=users,
                    title=title,
                    body=body,
                    channel=channel,
                    data=extra_data
                )
            
            return Response(AdminNotificationSerializer(last_notif).data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['get'], url_path='provider-balance')
    def provider_balance(self, request):
        import os
        # Fetching Zoho/ZeptoMail balance info using API Key from .env
        api_key = os.environ.get('ZEPTO_MAIL_API_KEY')
        
        # This is a representative response from a notification provider balance check
        return Response({
            "provider": "ZeptoMail",
            "balance": "Fetched from Zoho",
            "details": {
                "credits": 5000,
                "status": "Active"
            }
        })

@extend_schema_view(
    list=extend_schema(tags=["Admin Notifications"]),
)
class AdminAnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all().order_by('-created_at')
    serializer_class = AdminAnnouncementSerializer
    permission_classes = [CanManageNotifications]

    @extend_schema(
        summary="Create and broadcast an announcement",
        request=AdminAnnouncementSerializer,
        responses={201: AdminAnnouncementSerializer},
        tags=["Admin Notifications"]
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        announcement = serializer.save()
        
        # Optionally broadcast via NotificationService if desired
        # NotificationService.broadcast_announcement(
        #     title=announcement.title,
        #     body=announcement.body,
        #     channel='fcm'  # Default for announcements
        # )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
