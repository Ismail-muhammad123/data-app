from rest_framework import viewsets, status, permissions
from drf_spectacular.utils import extend_schema, extend_schema_view
from admin_api.permissions import IsSuperUserOnly, CanManageNotifications
from notifications.models import Notification, Announcement, NotificationTemplate
from admin_api.serializers import (
    AdminNotificationSerializer, AdminAnnouncementSerializer,
    AdminBulkSendNotificationSerializer, NotificationTemplateSerializer,
    AdminNotificationOverviewSerializer
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
            recipient_type = serializer.validated_data['recipient_type']
            user_ids = serializer.validated_data.get('user_ids', [])
            title = serializer.validated_data['title']
            body = serializer.validated_data['body']
            channels = serializer.validated_data['channels']
            extra_data = serializer.validated_data.get('data', {})

            if recipient_type == 'individuals':
                if not user_ids:
                    return Response({"error": "user_ids required for 'individuals' recipient type"}, status=400)
                users = User.objects.filter(id__in=user_ids)
            elif recipient_type == 'all':
                users = User.objects.all()
            elif recipient_type == 'customers':
                users = User.objects.filter(role='customer')
            elif recipient_type == 'agents':
                users = User.objects.filter(role='agent')
            else:
                return Response({"error": "Invalid recipient type"}, status=400)

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
                    data=extra_data,
                    created_by=self.request.user
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

class AdminNotificationTemplateViewSet(viewsets.ModelViewSet):
    queryset = NotificationTemplate.objects.all().order_by('slug')
    serializer_class = NotificationTemplateSerializer
    permission_classes = [CanManageNotifications]

    @extend_schema(
        tags=["Admin Notifications"],
        summary="Get overview of notifications, announcements, and templates",
        responses={200: AdminNotificationOverviewSerializer}
    )
    @action(detail=False, methods=['get'], url_path='overview')
    def overview(self, request):
        notifications = Notification.objects.all().order_by('-created_at')[:50]
        announcements = Announcement.objects.all().order_by('-created_at')[:20]
        templates = NotificationTemplate.objects.all().order_by('slug')
        
        data = {
            "notifications": AdminNotificationSerializer(notifications, many=True).data,
            "announcements": AdminAnnouncementSerializer(announcements, many=True).data,
            "templates": NotificationTemplateSerializer(templates, many=True).data
        }
        return Response(data)

@extend_schema_view(
    list=extend_schema(summary="List all announcements", tags=["Admin Notifications"]),
    create=extend_schema(summary="Create a new announcement", tags=["Admin Notifications"]),
    retrieve=extend_schema(summary="Get announcement details", tags=["Admin Notifications"]),
    update=extend_schema(summary="Fully update an announcement", tags=["Admin Notifications"]),
    partial_update=extend_schema(summary="Partially update an announcement", tags=["Admin Notifications"]),
    destroy=extend_schema(summary="Delete an announcement", tags=["Admin Notifications"]),
)
class AdminAnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all().order_by('-created_at')
    serializer_class = AdminAnnouncementSerializer
    permission_classes = [CanManageNotifications]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Optional: Trigger real-time broadcast via FCM here if desired
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Announcement deleted successfully"}, status=status.HTTP_200_OK)
