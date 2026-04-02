from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema_view, extend_schema
from users.models import User
from orders.models import Purchase, VTUProviderConfig, ServiceRouting
from admin_api.serializers import (
    AdminPurchaseSerializer, VTUProviderConfigSerializer,
    ServiceRoutingSerializer, AdminCreatePurchaseRequestSerializer,
    AdminStatusResponseSerializer, AdminErrorResponseSerializer
)
from admin_api.permissions import CanManageVTU
from orders.router import ProviderRouter
from wallet.utils import fund_wallet

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

@extend_schema_view(
    list=extend_schema(tags=["Admin VTU Config"]),
    retrieve=extend_schema(tags=["Admin VTU Config"]),
    create=extend_schema(tags=["Admin VTU Config"]),
    update=extend_schema(tags=["Admin VTU Config"]),
    partial_update=extend_schema(tags=["Admin VTU Config"]),
    destroy=extend_schema(tags=["Admin VTU Config"]),
)
class AdminVTUProviderConfigViewSet(viewsets.ModelViewSet):
    """Manage VTU provider configurations (API keys, base URLs, etc.)."""
    queryset = VTUProviderConfig.objects.all()
    serializer_class = VTUProviderConfigSerializer
    permission_classes = [CanManageVTU]

@extend_schema_view(
    list=extend_schema(tags=["Admin VTU Config"]),
    retrieve=extend_schema(tags=["Admin VTU Config"]),
    create=extend_schema(tags=["Admin VTU Config"]),
    update=extend_schema(tags=["Admin VTU Config"]),
    partial_update=extend_schema(tags=["Admin VTU Config"]),
    destroy=extend_schema(tags=["Admin VTU Config"]),
)
class AdminServiceRoutingViewSet(viewsets.ModelViewSet):
    """Manage service routing (primary provider & fallback chain per service type)."""
    queryset = ServiceRouting.objects.all()
    serializer_class = ServiceRoutingSerializer
    permission_classes = [CanManageVTU]
