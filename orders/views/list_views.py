from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema, extend_schema_view
from orders.models import (
    DataService, DataVariation, AirtimeNetwork, 
    ElectricityService, TVService, TVVariation, 
    SmileVariation, EducationService, EducationVariation,
    ServiceRouting
)
from orders.serializers import (
    DataServiceSerializer, DataVariationSerializer,
    AirtimeNetworkSerializer, TVServiceSerializer,
    TVVariationSerializer, SmileVariationSerializer,
    EducationServiceSerializer, EducationVariationSerializer,
    ElectricityServiceSerializer
)


@extend_schema(tags=["Orders - Data"])
class DataServicesListView(generics.ListAPIView):
    """List available data networks/services for the active provider."""
    serializer_class = DataServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        routing = ServiceRouting.objects.filter(service='data').first()
        if routing and routing.primary_provider:
            return DataService.objects.filter(provider=routing.primary_provider, is_active=True)
        return DataService.objects.filter(is_active=True)


@extend_schema(tags=["Orders - Data"])
class DataVariationsListView(generics.ListAPIView):
    """List available data plans/variations. Filter by service_id query param."""
    serializer_class = DataVariationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = DataVariation.objects.filter(is_active=True)
        service_id = self.request.query_params.get("service_id")
        if service_id:
            queryset = queryset.filter(service__id=service_id)
        return queryset


@extend_schema(tags=["Orders - Airtime"])
class AirtimeNetworkListView(generics.ListAPIView):
    """List available airtime networks for the active provider."""
    serializer_class = AirtimeNetworkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        routing = ServiceRouting.objects.filter(service='airtime').first()
        if routing and routing.primary_provider:
            return AirtimeNetwork.objects.filter(provider=routing.primary_provider, is_active=True)
        return AirtimeNetwork.objects.filter(is_active=True)


@extend_schema(tags=["Orders - Electricity"])
class ElectricityServiceListView(generics.ListAPIView):
    """List available electricity distribution companies (DISCOs)."""
    serializer_class = ElectricityServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        routing = ServiceRouting.objects.filter(service='electricity').first()
        if routing and routing.primary_provider:
            return ElectricityService.objects.filter(provider=routing.primary_provider, is_active=True)
        return ElectricityService.objects.filter(is_active=True)


@extend_schema(tags=["Orders - Cable TV"])
class TVServicesListView(generics.ListAPIView):
    """List available Cable TV services (DSTV, GOTV, Startimes)."""
    serializer_class = TVServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        routing = ServiceRouting.objects.filter(service='tv').first()
        if routing and routing.primary_provider:
            return TVService.objects.filter(provider=routing.primary_provider, is_active=True)
        return TVService.objects.filter(is_active=True)


@extend_schema(tags=["Orders - Cable TV"])
class TVPackagesListView(generics.ListAPIView):
    """List available TV bouquet packages. Filter by service_id query param."""
    queryset = TVVariation.objects.all()
    serializer_class = TVVariationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        service_id = self.request.query_params.get("service_id")
        if not service_id:
            return TVVariation.objects.filter(is_active=True)
        return TVVariation.objects.filter(is_active=True, service__service_id=service_id)


@extend_schema(tags=["Orders - Smile"])
class SmilePackagesListView(generics.ListAPIView):
    """List available Smile data packages."""
    serializer_class = SmileVariationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        routing = ServiceRouting.objects.filter(service='smile').first()
        if routing and routing.primary_provider:
            return SmileVariation.objects.filter(service__provider=routing.primary_provider, is_active=True)
        return SmileVariation.objects.filter(is_active=True)


@extend_schema(tags=["Orders - Education"])
class EducationServiceListView(generics.ListAPIView):
    """List available education services (WAEC, NECO, etc.)."""
    serializer_class = EducationServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        routing = ServiceRouting.objects.filter(service='education').first()
        if routing and routing.primary_provider:
            return EducationService.objects.filter(provider=routing.primary_provider, is_active=True)
        return EducationService.objects.filter(is_active=True)


@extend_schema(tags=["Orders - Education"])
class EducationVariationListView(generics.ListAPIView):
    """List available education PIN variations. Filter by service_id query param."""
    serializer_class = EducationVariationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        service_id = self.request.query_params.get("service_id")
        if service_id:
            return EducationVariation.objects.filter(service__service_id=service_id, is_active=True)
        return EducationVariation.objects.filter(is_active=True)
