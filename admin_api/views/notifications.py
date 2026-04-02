from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema_view, extend_schema
from notifications.models import NotificationLog, Announcement, NotificationProviderConfig
from admin_api.serializers import (
    AdminNotificationLogSerializer, AdminAnnouncementSerializer,
    AdminNotificationProviderConfigSerializer
)
from admin_api.permissions import IsSuperUserOnly

@extend_schema_view(
    list=extend_schema(tags=["Admin Notifications"]),
)
class AdminNotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NotificationLog.objects.all().order_by('-created_at')
    serializer_class = AdminNotificationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['user', 'channel', 'status']

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
