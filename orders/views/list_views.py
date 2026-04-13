from rest_framework import generics, permissions
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from orders.models import (
    DataService, DataVariation, AirtimeNetwork, 
    ElectricityService, ElectricityVariation, TVService, TVVariation, 
    InternetService, InternetVariation, EducationService, EducationVariation,
    ServiceRouting
)
from orders.serializers import (
    DataServiceSerializer, DataVariationSerializer,
    AirtimeNetworkSerializer, TVServiceSerializer,
    TVVariationSerializer, InternetServiceSerializer, InternetVariationSerializer,
    EducationServiceSerializer, EducationVariationSerializer,
    ElectricityServiceSerializer, ElectricityVariationSerializer
)

def _active_services_with_routing_fallback(model, service_type):
    """
    Prefer active services for the routed provider.
    If no rows exist for that provider, gracefully fall back to all active services.
    """
    active_qs = model.objects.filter(is_active=True).order_by('id')
    routing = ServiceRouting.objects.filter(service=service_type).first()
    if routing and routing.primary_provider:
        routed_qs = active_qs.filter(provider=routing.primary_provider)
        if routed_qs.exists():
            return routed_qs
    return active_qs


def _filter_variations_by_service_param(queryset, service_param):
    """
    Accept both internal PK (`service.id`) and provider service code (`service.service_id`)
    for compatibility with different clients.
    """
    if not service_param:
        return queryset
    return queryset.filter(Q(service__id=service_param) | Q(service__service_id=service_param))


@extend_schema(tags=["Orders - Data"])
class DataServicesListView(generics.ListAPIView):
    """List available data networks/services for the active provider."""
    serializer_class = DataServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return _active_services_with_routing_fallback(DataService, 'data')


@extend_schema(tags=["Orders - Data"])
class DataVariationsListView(generics.ListAPIView):
    """List available data plans/variations. Filter by service_id query param or network_id in URL."""
    serializer_class = DataVariationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = DataVariation.objects.filter(is_active=True).order_by('id')
        network_id = self.kwargs.get("network_id")
        if network_id:
            # Strict PK filter — the client passed the exact DB id of the DataService.
            return queryset.filter(service__id=network_id)
        # For ?service_id= query param, accept both PK and provider string code.
        service_id = self.request.query_params.get("service_id")
        return _filter_variations_by_service_param(queryset, service_id)



@extend_schema(tags=["Orders - Airtime"])
class AirtimeNetworkListView(generics.ListAPIView):
    """List available airtime networks for the active provider."""
    serializer_class = AirtimeNetworkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return _active_services_with_routing_fallback(AirtimeNetwork, 'airtime')


@extend_schema(tags=["Orders - Electricity"])
class ElectricityServiceListView(generics.ListAPIView):
    """List available electricity distribution companies (DISCOs)."""
    serializer_class = ElectricityServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return _active_services_with_routing_fallback(ElectricityService, 'electricity')


@extend_schema(tags=["Orders - Electricity"])
class ElectricityVariationListView(generics.ListAPIView):
    """List available electricity plans/variations. Filter by service_id query param or network_id in URL."""
    serializer_class = ElectricityVariationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ElectricityVariation.objects.filter(is_active=True).order_by('id')
        network_id = self.kwargs.get("network_id")
        if network_id:
            return queryset.filter(service__id=network_id)
        service_id = self.request.query_params.get("service_id")
        return _filter_variations_by_service_param(queryset, service_id)



@extend_schema(tags=["Orders - Cable TV"])
class TVServicesListView(generics.ListAPIView):
    """List available Cable TV services (DSTV, GOTV, Startimes)."""
    serializer_class = TVServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return _active_services_with_routing_fallback(TVService, 'tv')


@extend_schema(tags=["Orders - Cable TV"])
class TVPackagesListView(generics.ListAPIView):
    """List available TV bouquet packages. Filter by service_id query param or network_id in URL."""
    serializer_class = TVVariationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = TVVariation.objects.filter(is_active=True).order_by('id')
        network_id = self.kwargs.get("network_id")
        if network_id:
            return queryset.filter(service__id=network_id)
        service_id = self.request.query_params.get("service_id")
        return _filter_variations_by_service_param(queryset, service_id)



@extend_schema(tags=["Orders - Internet"])
class InternetServicesListView(generics.ListAPIView):
    """List available Internet services (Smile, Spectranet, etc.)."""
    serializer_class = InternetServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return _active_services_with_routing_fallback(InternetService, 'internet')


@extend_schema(tags=["Orders - Internet"])
class InternetPackagesListView(generics.ListAPIView):
    """List available Internet data packages. Filter by service_id query param or network_id in URL."""
    serializer_class = InternetVariationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = InternetVariation.objects.filter(is_active=True).order_by('id')
        network_id = self.kwargs.get("network_id")
        if network_id:
            return queryset.filter(service__id=network_id)
        service_id = self.request.query_params.get("service_id")
        return _filter_variations_by_service_param(queryset, service_id)



@extend_schema(tags=["Orders - Education"])
class EducationServiceListView(generics.ListAPIView):
    """List available education services (WAEC, NECO, etc.)."""
    serializer_class = EducationServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return _active_services_with_routing_fallback(EducationService, 'education')


@extend_schema(tags=["Orders - Education"])
class EducationVariationListView(generics.ListAPIView):
    """List available education PIN variations. Filter by service_id query param or network_id in URL."""
    serializer_class = EducationVariationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = EducationVariation.objects.filter(is_active=True).order_by('id')
        network_id = self.kwargs.get("network_id")
        if network_id:
            return queryset.filter(service__id=network_id)
        service_id = self.request.query_params.get("service_id")
        return _filter_variations_by_service_param(queryset, service_id)

