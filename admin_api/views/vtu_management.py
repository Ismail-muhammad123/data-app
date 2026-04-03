from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema_view, extend_schema
from users.models import User
from orders.models import (
    Purchase, VTUProviderConfig, ServiceRouting, 
    DataVariation, AirtimeNetwork, TVVariation, 
    InternetVariation, EducationVariation, ElectricityVariation,
    DataService, TVService, ElectricityService, InternetService, EducationService
)
from admin_api.serializers import (
    AdminPurchaseSerializer, VTUProviderConfigSerializer,
    ServiceRoutingSerializer, AdminCreatePurchaseRequestSerializer,
    AdminStatusResponseSerializer, AdminErrorResponseSerializer,
    VTUOverviewResponseSerializer, FetchFromProviderRequestSerializer,
    VariationPriceUpdateSerializer, BulkVariationPriceUpdateSerializer,
    VariationToggleSerializer, ServiceTypeToggleSerializer,
    ProviderFundingConfigSerializer, AvailableVTUProviderSerializer
)
from admin_api.permissions import CanManageVTU
from orders.router import ProviderRouter
from wallet.utils import fund_wallet
from django.db.models import Count, Avg, F
from django.db import transaction

@extend_schema_view(
    list=extend_schema(tags=["Admin Purchases"]),
    retrieve=extend_schema(tags=["Admin Purchases"]),
)
class AdminPurchaseViewSet(viewsets.ModelViewSet):
    queryset = Purchase.objects.all().order_by('-time')
    serializer_class = AdminPurchaseSerializer
    permission_classes = [CanManageVTU]

    @extend_schema(
        tags=["Admin Purchases"],
        summary="Initiate a purchase for a user",
        request=AdminCreatePurchaseRequestSerializer,
        responses={200: AdminPurchaseSerializer}
    )
    def create(self, request, *args, **kwargs):
        from orders.utils.purchase_logic import process_vtu_purchase
        serializer = AdminCreatePurchaseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = serializer.validated_data['user_id']
        purchase_type = serializer.validated_data['purchase_type']
        amount = serializer.validated_data['amount']
        beneficiary = serializer.validated_data['beneficiary']
        action_name = serializer.validated_data['action']
        
        user = User.objects.get(id=user_id)
        
        res = process_vtu_purchase(
            user=user,
            purchase_type=purchase_type,
            amount=amount,
            beneficiary=beneficiary,
            action=action_name,
            **serializer.validated_data.get('extra_kwargs', {})
        )
        return Response(res)

    @extend_schema(
        tags=["Admin Purchases"],
        summary="Retry a failed purchase",
        responses={200: AdminStatusResponseSerializer, 400: AdminErrorResponseSerializer}
    )
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        purchase = self.get_object()
        if purchase.status != 'failed':
            return Response({"error": "Can only retry failed purchases"}, status=400)
        
        res = ProviderRouter.execute_with_fallback(purchase.purchase_type, f"buy_{purchase.purchase_type}", **purchase.provider_response.get('request_data', {}))
        if res['status'] == 'SUCCESS':
             purchase.status = 'success'
             purchase.save()
        return Response(res)

    @extend_schema(
        tags=["Admin Purchases"],
        summary="Refund a purchase to user wallet",
        responses={200: AdminStatusResponseSerializer, 400: AdminErrorResponseSerializer}
    )
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        purchase = self.get_object()
        if purchase.status == 'refunded':
             return Response({"error": "Already refunded"}, status=400)
        
        fund_wallet(
            purchase.user.id, 
            purchase.amount, 
            description=f"Refund: Manual refund for purchase {purchase.reference}",
            initiator='admin',
            initiated_by=request.user
        )
        purchase.status = 'failed' 
        purchase.save()
        return Response({"status": "SUCCESS", "message": "Purchase refunded to user wallet."})

    @extend_schema(
        tags=["Admin Purchases"],
        summary="Cancel a pending purchase",
        responses={200: AdminStatusResponseSerializer, 400: AdminErrorResponseSerializer}
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        purchase = self.get_object()
        if purchase.status != 'pending':
            return Response({"error": "Can only cancel pending purchases"}, status=400)
        
        purchase.status = 'failed'
        purchase.save()
        
        fund_wallet(
            purchase.user.id, 
            purchase.amount, 
            description=f"Refund: Purchase {purchase.reference} cancelled by Admin",
            initiator='admin',
            initiated_by=request.user
        )
        return Response({"status": "SUCCESS", "message": "Purchase cancelled and refunded."})

class VTUOverviewView(APIView):
    permission_classes = [CanManageVTU]

    @extend_schema(
        tags=["Admin VTU Control"],
        summary="Get consolidated VTU services and providers overview",
        responses={200: VTUOverviewResponseSerializer}
    )
    def get(self, request):
        providers = VTUProviderConfig.objects.all()
        # Fetch actual balances for active providers
        provider_data = []
        for p in providers:
            balance = 0.0
            if p.is_active:
                impl = ProviderRouter.get_provider_implementation(p.name)
                if impl:
                    try:
                        balance = impl.get_wallet_balance()
                    except:
                        pass
            
            p_dict = VTUProviderConfigSerializer(p).data
            p_dict['balance'] = balance
            provider_data.append(p_dict)
            
        services_list = ['airtime', 'data', 'tv', 'electricity', 'internet', 'education']
        summary = []
        
        for st in services_list:
            routing = ServiceRouting.objects.filter(service=st).first()
            # Success rates from last 100 txs
            txs = Purchase.objects.filter(purchase_type=st).order_by('-time')[:100]
            success_rate = 0
            if txs.count() > 0:
                success_rate = txs.filter(status='success').count() / txs.count()
            
            summary.append({
                "service": st,
                "is_active": True, # Placeholder or from SiteConfig
                "routing": ServiceRoutingSerializer(routing).data if routing else None,
                "success_rate": success_rate,
                "total_variations": self._get_variation_count(st)
            })
            
        return Response({
            "providers": provider_data,
            "services_summary": summary
        })

    def _get_variation_count(self, service_type):
        models_map = {
            'data': DataVariation, 'airtime': AirtimeNetwork, 'tv': TVVariation,
            'electricity': ElectricityVariation, 'internet': InternetVariation, 'education': EducationVariation
        }
        model = models_map.get(service_type)
        return model.objects.count() if model else 0

class ProviderBalanceView(APIView):
    permission_classes = [CanManageVTU]

    @extend_schema(
        tags=["Admin VTU Control"],
        summary="Fetch real-time balance for a specific provider",
        responses={200: {"balance": 0.0}}
    )
    def get(self, request, pk):
        try:
            provider = VTUProviderConfig.objects.get(pk=pk)
        except VTUProviderConfig.DoesNotExist:
            return Response({"error": "Provider not found"}, status=status.HTTP_404_NOT_FOUND)
            print(provider.name)
            print(provider.name.lower())
        impl = ProviderRouter.get_provider_implementation(provider.name.lower())
        if not impl:
            return Response({"error": "Implementation not found"}, status=status.HTTP_400_BAD_REQUEST)
        
        balance = impl.get_wallet_balance()
        return Response({"balance": balance})

class FetchFromProviderView(APIView):
    permission_classes = [CanManageVTU]

    @extend_schema(
        tags=["Admin VTU Control"],
        summary="Fetch services/variations from provider API and save to local DB",
        request=FetchFromProviderRequestSerializer,
        responses={200: AdminStatusResponseSerializer}
    )
    def post(self, request):
        serializer = FetchFromProviderRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        provider_id = serializer.validated_data['provider_id']
        service_type = serializer.validated_data['service_type']
        
        provider = VTUProviderConfig.objects.get(id=provider_id)
        # Use existing sync logic if available in the provider implementation
        # For simplicity in this demo, we call a placeholders sync method or actual if defined
        # In a real app, we'd have a mapping layer.
        
        # Example using ClubKonnectClient if provider is clubkonnect
        if provider.name == 'clubkonnect':
             from orders.services.clubkonnect import ClubKonnectClient
             client = ClubKonnectClient()
             if service_type == 'data': client.sync_data()
             elif service_type == 'airtime': client.sync_airtime()
             elif service_type == 'tv': client.sync_cable()
             elif service_type == 'electricity': client.sync_electricity()
             elif service_type == 'internet': client.sync_internet()
        else:
             # Fallback to generic implementation methods if they support sync
             impl = ProviderRouter.get_provider_implementation(provider.name)
             if impl:
                 # Logic to iterate and save variations locally
                 pass
        
        return Response({"status": "SUCCESS", "message": f"Successfully synced {service_type} from {provider.name}"})

class VariationUpdatePriceView(APIView):
    permission_classes = [CanManageVTU]

    @extend_schema(
        tags=["Admin VTU Control"],
        summary="Update pricing for a specific variation",
        request=VariationPriceUpdateSerializer,
        responses={200: AdminStatusResponseSerializer}
    )
    def post(self, request, pk, service_type):
        models_map = {
            'data': DataVariation, 'tv': TVVariation,
            'internet': InternetVariation, 'education': EducationVariation
        }
        model = models_map.get(service_type)
        if not model: return Response({"error": "Invalid service type"}, status=400)
        
        variation = model.objects.get(pk=pk)
        serializer = VariationPriceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        variation.selling_price = serializer.validated_data['selling_price']
        variation.agent_price = serializer.validated_data['agent_price']
        variation.save()
        
        return Response({"status": "SUCCESS", "message": "Price updated."})

class BulkVariationUpdatePriceView(APIView):
    permission_classes = [CanManageVTU]

    @extend_schema(
        tags=["Admin VTU Control"],
        summary="Bulk update prices for multiple variations",
        request=BulkVariationPriceUpdateSerializer,
        responses={200: AdminStatusResponseSerializer}
    )
    def post(self, request, service_type):
        models_map = {
            'data': DataVariation, 'tv': TVVariation,
            'internet': InternetVariation, 'education': EducationVariation
        }
        model = models_map.get(service_type)
        if not model: return Response({"error": "Invalid service type"}, status=400)
        
        serializer = BulkVariationPriceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            for item in serializer.validated_data['variations']:
                model.objects.filter(id=item['id']).update(
                    selling_price=item['selling_price'],
                    agent_price=item['agent_price']
                )
        
        return Response({"status": "SUCCESS", "message": f"Bulk update for {service_type} variations completed."})

class VariationToggleView(APIView):
    permission_classes = [CanManageVTU]

    @extend_schema(
        tags=["Admin VTU Control"],
        summary="Enable/disable a specific variation",
        request=VariationToggleSerializer,
        responses={200: AdminStatusResponseSerializer}
    )
    def post(self, request, pk, service_type):
        models_map = {
            'data': DataVariation, 'airtime': AirtimeNetwork, 'tv': TVVariation,
            'electricity': ElectricityVariation, 'internet': InternetVariation, 'education': EducationVariation
        }
        model = models_map.get(service_type)
        variation = model.objects.get(pk=pk)
        
        active = request.data.get('is_active', not variation.is_active)
        variation.is_active = active
        variation.save()
        
        return Response({"status": "SUCCESS", "message": f"Variation {'enabled' if active else 'disabled'}."})

class ServiceTypeToggleView(APIView):
    permission_classes = [CanManageVTU]

    @extend_schema(
        tags=["Admin VTU Control"],
        summary="Enable/disable an entire service type (e.g. data)",
        request=ServiceTypeToggleSerializer,
        responses={200: AdminStatusResponseSerializer}
    )
    def post(self, request, service_type):
        from summary.models import SiteConfig
        config = SiteConfig.objects.first()
        
        active = request.data.get('is_active')
        field_map = {
            'airtime': 'airtime_active', 'data': 'data_active', 
            'tv': 'tv_active', 'electricity': 'electricity_active',
            'education': 'education_active'
        }
        field = field_map.get(service_type)
        if not field: return Response({"error": "Invalid service type"}, status=400)
        
        setattr(config, field, active)
        config.save()
        
        return Response({"status": "SUCCESS", "message": f"Service type {service_type} {'enabled' if active else 'disabled'}."})

class AdminAvailableVTUProvidersView(APIView):
    """
    Get the list of all officially supported VTU providers from the registry.
    Use this to populate dropdowns when adding new provider configurations.
    """
    permission_classes = [CanManageVTU]

    @extend_schema(
        tags=["Admin VTU Config"],
        summary="List all supported VTU providers from the registry",
        responses={200: AvailableVTUProviderSerializer(many=True)}
    )
    def get(self, request):
        from orders.providers.registry import AVAILABLE_PROVIDERS
        data = [{"id": p[0], "name": p[1]} for p in AVAILABLE_PROVIDERS]
        return Response(data)

@extend_schema_view(
    list=extend_schema(tags=["Admin VTU Config"]),
    retrieve=extend_schema(tags=["Admin VTU Config"]),
    create=extend_schema(tags=["Admin VTU Config"]),
    update=extend_schema(tags=["Admin VTU Config"]),
    partial_update=extend_schema(tags=["Admin VTU Config"]),
    destroy=extend_schema(tags=["Admin VTU Config"]),
    available_providers=extend_schema(tags=["Admin VTU Config"], summary="Get list of all supported providers for dropdown selection"),
)
class AdminVTUProviderConfigViewSet(viewsets.ModelViewSet):
    """Manage VTU provider configurations (API keys, base URLs, etc.)."""
    queryset = VTUProviderConfig.objects.all()
    serializer_class = VTUProviderConfigSerializer
    permission_classes = [CanManageVTU]

    @extend_schema(summary="Get list of all supported providers for dropdown selection", responses={200: AvailableVTUProviderSerializer(many=True)})
    @action(detail=False, methods=['get'], url_path='available-providers')
    def available_providers(self, request):
        choices = VTUProviderConfig.PROVIDER_CHOICES
        return Response([{"id": c[0], "name": c[1]} for c in choices])

    @extend_schema(summary="Update provider funding configuration")
    @action(detail=True, methods=['post'], url_path='funding-config')
    def set_funding_config(self, request, pk=None):
        provider = self.get_object()
        serializer = ProviderFundingConfigSerializer(provider, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": "SUCCESS", "message": "Funding config updated."})

@extend_schema_view(
    list=extend_schema(tags=["Admin VTU Config"]),
    retrieve=extend_schema(tags=["Admin VTU Config"]),
    create=extend_schema(tags=["Admin VTU Config"]),
    update=extend_schema(tags=["Admin VTU Config"]),
    partial_update=extend_schema(tags=["Admin VTU Config"]),
    destroy=extend_schema(tags=["Admin VTU Config"]),
    available_providers=extend_schema(tags=["Admin VTU Config"], summary="Get list of all supported providers for dropdown selection"),
)
class AdminServiceRoutingViewSet(viewsets.ModelViewSet):
    """Manage service routing (primary provider & fallback chain per service type)."""
    queryset = ServiceRouting.objects.all()
    serializer_class = ServiceRoutingSerializer
    permission_classes = [CanManageVTU]
