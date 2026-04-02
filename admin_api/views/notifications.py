from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema, extend_schema_view
from notifications.models import Notification, Announcement, NotificationProviderConfig
from admin_api.serializers import (
    AdminNotificationSerializer, AdminAnnouncementSerializer,
    AdminNotificationProviderConfigSerializer, AdminBulkSendNotificationSerializer
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
    permission_classes = [permissions.IsAuthenticated]

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
            channel = serializer.validated_data['channel']
            extra_data = serializer.validated_data.get('data', {})

            users = User.objects.filter(id__in=user_ids)
            if not users.exists():
                return Response({"error": "No valid users found"}, status=400)

            notification = NotificationService.create_notification(
                users=users,
                title=title,
                body=body,
                channel=channel,
                data=extra_data
            )
            
            return Response(AdminNotificationSerializer(notification).data, status=201)
        return Response(serializer.errors, status=400)

@extend_schema_view(
    list=extend_schema(tags=["Admin Notifications"]),
)
class AdminAnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all().order_by('-created_at')
    serializer_class = AdminAnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]

@extend_schema_view(
    list=extend_schema(tags=["Admin Notifications"]),
)
class AdminNotificationProviderConfigViewSet(viewsets.ModelViewSet):
    queryset = NotificationProviderConfig.objects.all()
    serializer_class = AdminNotificationProviderConfigSerializer
    permission_classes = [IsSuperUserOnly]
