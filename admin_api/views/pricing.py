from rest_framework import viewsets
from drf_spectacular.utils import extend_schema
from orders.models import (
    DataVariation, DataService, AirtimeNetwork, TVVariation, TVService, 
    InternetVariation, InternetService, EducationVariation, EducationService, 
    ElectricityVariation, ElectricityService
)
from admin_api.serializers import (
    AdminDataVariationSerializer, AdminDataServiceSerializer, AdminAirtimeNetworkSerializer,
    AdminTVVariationSerializer, AdminTVServiceSerializer, AdminInternetVariationSerializer, 
    AdminInternetServiceSerializer, AdminEducationVariationSerializer, AdminEducationServiceSerializer, 
    AdminElectricityVariationSerializer, AdminElectricityServiceSerializer
)
from admin_api.permissions import CanManageVTU

class AdminBasePricingViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageVTU]
    http_method_names = ['get', 'post', 'delete']

@extend_schema(tags=["Admin Pricing & Plans"])
class AdminAirtimeNetworkViewSet(AdminBasePricingViewSet):
    queryset = AirtimeNetwork.objects.all()
    serializer_class = AdminAirtimeNetworkSerializer

@extend_schema(tags=["Admin Pricing & Plans"])
class AdminDataServiceViewSet(AdminBasePricingViewSet):
    queryset = DataService.objects.all()
    serializer_class = AdminDataServiceSerializer

@extend_schema(tags=["Admin Pricing & Plans"])
class AdminDataVariationViewSet(AdminBasePricingViewSet):
    queryset = DataVariation.objects.all()
    serializer_class = AdminDataVariationSerializer

@extend_schema(tags=["Admin Pricing & Plans"])
class AdminTVServiceViewSet(AdminBasePricingViewSet):
    queryset = TVService.objects.all()
    serializer_class = AdminTVServiceSerializer

@extend_schema(tags=["Admin Pricing & Plans"])
class AdminTVVariationViewSet(AdminBasePricingViewSet):
    queryset = TVVariation.objects.all()
    serializer_class = AdminTVVariationSerializer

@extend_schema(tags=["Admin Pricing & Plans"])
class AdminInternetServiceViewSet(AdminBasePricingViewSet):
    queryset = InternetService.objects.all()
    serializer_class = AdminInternetServiceSerializer

@extend_schema(tags=["Admin Pricing & Plans"])
class AdminInternetVariationViewSet(AdminBasePricingViewSet):
    queryset = InternetVariation.objects.all()
    serializer_class = AdminInternetVariationSerializer

@extend_schema(tags=["Admin Pricing & Plans"])
class AdminEducationServiceViewSet(AdminBasePricingViewSet):
    queryset = EducationService.objects.all()
    serializer_class = AdminEducationServiceSerializer

@extend_schema(tags=["Admin Pricing & Plans"])
class AdminEducationVariationViewSet(AdminBasePricingViewSet):
    queryset = EducationVariation.objects.all()
    serializer_class = AdminEducationVariationSerializer

@extend_schema(tags=["Admin Pricing & Plans"])
class AdminElectricityServiceViewSet(AdminBasePricingViewSet):
    queryset = ElectricityService.objects.all()
    serializer_class = AdminElectricityServiceSerializer

@extend_schema(tags=["Admin Pricing & Plans"])
class AdminElectricityVariationViewSet(AdminBasePricingViewSet):
    queryset = ElectricityVariation.objects.all()
    serializer_class = AdminElectricityVariationSerializer
