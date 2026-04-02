from rest_framework import viewsets
from drf_spectacular.utils import extend_schema
from orders.models import (
    DataVariation, AirtimeNetwork, TVVariation, SmileVariation, 
    EducationVariation, ElectricityVariation, PromoCode
)
from admin_api.serializers import (
    AdminDataVariationSerializer, AdminAirtimeNetworkSerializer,
    AdminTVVariationSerializer, AdminSmileVariationSerializer,
    AdminEducationVariationSerializer, AdminElectricityVariationSerializer,
    AdminPromoCodeSerializer
)
from admin_api.permissions import CanManageVTU

@extend_schema(tags=["Admin Pricing & Plans"])
class AdminDataVariationViewSet(viewsets.ModelViewSet):
    queryset = DataVariation.objects.all()
    serializer_class = AdminDataVariationSerializer
    permission_classes = [CanManageVTU]

@extend_schema(tags=["Admin Pricing & Plans"])
class AdminTVVariationViewSet(viewsets.ModelViewSet):
    queryset = TVVariation.objects.all()
    serializer_class = AdminTVVariationSerializer
    permission_classes = [CanManageVTU]

@extend_schema(tags=["Admin Pricing & Plans"])
class AdminAirtimeNetworkViewSet(viewsets.ModelViewSet):
    queryset = AirtimeNetwork.objects.all()
    serializer_class = AdminAirtimeNetworkSerializer
    permission_classes = [CanManageVTU]

@extend_schema(tags=["Admin Pricing & Plans"])
class AdminSmileVariationViewSet(viewsets.ModelViewSet):
    queryset = SmileVariation.objects.all()
    serializer_class = AdminSmileVariationSerializer
    permission_classes = [CanManageVTU]

@extend_schema(tags=["Admin Pricing & Plans"])
class AdminEducationVariationViewSet(viewsets.ModelViewSet):
    queryset = EducationVariation.objects.all()
    serializer_class = AdminEducationVariationSerializer
    permission_classes = [CanManageVTU]

@extend_schema(tags=["Admin Pricing & Plans"])
class AdminElectricityVariationViewSet(viewsets.ModelViewSet):
    queryset = ElectricityVariation.objects.all()
    serializer_class = AdminElectricityVariationSerializer
    permission_classes = [CanManageVTU]

@extend_schema(tags=["Admin Pricing & Plans"])
class AdminPromoCodeViewSet(viewsets.ModelViewSet):
    queryset = PromoCode.objects.all()
    serializer_class = AdminPromoCodeSerializer
    permission_classes = [CanManageVTU]
