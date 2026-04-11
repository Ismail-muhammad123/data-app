from rest_framework import generics, permissions, status
from rest_framework.response import Response
from orders.models import (
    AirtimeNetwork, DataService, DataVariation, 
    ElectricityService, TVService, InternetService, 
    EducationService, EducationVariation, TVVariation,
    InternetVariation, ElectricityVariation
)
from ..authentication import APIKeyAuthentication
from ..permissions import IsDeveloperUser

class DeveloperServiceListView(generics.GenericAPIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsDeveloperUser]

    def get(self, request):
        """Returns all categories of services available"""
        return Response({
            "categories": [
                {"id": "airtime", "name": "Airtime Purchase", "endpoint": "/api/v1/developer/airtime/networks/"},
                {"id": "data", "name": "Data Bundles", "endpoint": "/api/v1/developer/data/networks/"},
                {"id": "electricity", "name": "Electricity Bills", "endpoint": "/api/v1/developer/electricity/services/"},
                {"id": "cable", "name": "Cable TV Subscription", "endpoint": "/api/v1/developer/cable/services/"},
                {"id": "internet", "name": "Internet Subscription", "endpoint": "/api/v1/developer/internet/services/"},
                {"id": "education", "name": "Education Pins", "endpoint": "/api/v1/developer/education/services/"},
            ]
        })

class DeveloperAirtimeNetworkListView(generics.ListAPIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsDeveloperUser]

    def list(self, request):
        networks = AirtimeNetwork.objects.filter(is_active=True).order_by('id')
        data = [{
            "id": n.id,
            "service_id": n.service_id,
            "name": n.service_name,
            "min_amount": n.min_amount,
            "max_amount": n.max_amount
        } for n in networks]
        return Response(data)

class DeveloperDataNetworkListView(generics.ListAPIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsDeveloperUser]

    def list(self, request):
        services = DataService.objects.filter(is_active=True).order_by('id')
        data = [{
            "id": s.id,
            "service_id": s.service_id,
            "name": s.service_name,
        } for s in services]
        return Response(data)

class DeveloperDataPlanListView(generics.ListAPIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsDeveloperUser]

    def get(self, request, network_id):
        plans = DataVariation.objects.filter(service_id=network_id, is_active=True).order_by('id')
        data = [{
            "id": p.id,
            "variation_id": p.variation_id,
            "name": p.name,
            "price": float(p.selling_price),
            "plan_type": p.plan_type
        } for p in plans]
        return Response(data)

# Electricity, TV, Internet, Education following same pattern
class DeveloperTVServiceListView(generics.ListAPIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsDeveloperUser]

    def list(self, request):
        services = TVService.objects.filter(is_active=True).order_by('id')
        data = [{"id": s.id, "service_id": s.service_id, "name": s.service_name} for s in services]
        return Response(data)

class DeveloperTVPackageListView(generics.ListAPIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsDeveloperUser]

    def get(self, request, service_id):
        variations = TVVariation.objects.filter(service_id=service_id, is_active=True).order_by('id')
        data = [{
            "id": v.id,
            "variation_id": v.variation_id,
            "name": v.name,
            "price": float(v.selling_price)
        } for v in variations]
        return Response(data)
