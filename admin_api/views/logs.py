from rest_framework import viewsets, mixins, permissions
from admin_api.models import AdminActionLog
from admin_api.serializers import AdminActionLogSerializer
from admin_api.permissions import CanManageSiteConfig

class AdminActionLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Viewset to list and retrieve admin action logs.
    Available only to admin staff with 'CanManageSiteConfig' permission.
    """
    queryset = AdminActionLog.objects.all().select_related('admin_user')
    serializer_class = AdminActionLogSerializer
    permission_classes = [CanManageSiteConfig]
    filterset_fields = ['admin_user', 'action_type', 'target_model']
    search_fields = ['description', 'target_id']
