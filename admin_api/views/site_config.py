from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema_view, extend_schema
from summary.models import SiteConfig, ServiceCashback
from admin_api.serializers import AdminSiteConfigSerializer, ServiceCashbackSerializer
from admin_api.permissions import CanManageSiteConfig, IsSuperUserOnly

@extend_schema_view(
    list=extend_schema(tags=["Admin Site Configuration"]),
    retrieve=extend_schema(tags=["Admin Site Configuration"]),
    create=extend_schema(tags=["Admin Site Configuration"]),
    update=extend_schema(tags=["Admin Site Configuration"]),
    partial_update=extend_schema(tags=["Admin Site Configuration"]),
)
class AdminSiteConfigViewSet(viewsets.ModelViewSet):
    """
    Manage global site configurations including charges, referrals, and bonuses.
    """
    queryset = SiteConfig.objects.all()
    serializer_class = AdminSiteConfigSerializer
    permission_classes = [CanManageSiteConfig]

    def get_object(self):
        # Override to always return the singleton object
        obj, created = SiteConfig.objects.get_or_create(pk=1)
        return obj

    @extend_schema(
        summary="Fetch Global Site Config",
        description="Returns the singleton SiteConfig instance."
    )
    def list(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

@extend_schema_view(
    list=extend_schema(tags=["Admin Site Configuration"]),
    retrieve=extend_schema(tags=["Admin Site Configuration"]),
    create=extend_schema(tags=["Admin Site Configuration"]),
    update=extend_schema(tags=["Admin Site Configuration"]),
    partial_update=extend_schema(tags=["Admin Site Configuration"]),
)
class AdminServiceCashbackViewSet(viewsets.ModelViewSet):
    """
    Manage service-specific cashback rules.
    """
    queryset = ServiceCashback.objects.all()
    serializer_class = ServiceCashbackSerializer
    permission_classes = [CanManageSiteConfig]
