import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from drf_spectacular.utils import extend_schema
from orders.models import Purchase
from orders.serializers import PurchaseSerializer, ErrorResponseSerializer
from orders.router import ProviderRouter
from wallet.utils import fund_wallet
from notifications.utils import NotificationService

logger = logging.getLogger(__name__)


class PurchaseHistoryView(generics.ListAPIView):
    serializer_class = PurchaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Orders - History"],
        summary="List purchase history",
        description="Returns a paginated list of all purchases made by the authenticated user, ordered by most recent.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Purchase.objects.filter(user=self.request.user).order_by("-time")


class PurchaseDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Orders - History"],
        summary="Get purchase details",
        description="Retrieve full details of a specific purchase by its ID.",
        responses={200: PurchaseSerializer, 404: ErrorResponseSerializer}
    )
    def get(self, request, pk):
        try:
            purchase = Purchase.objects.get(pk=pk, user=request.user)
        except Purchase.DoesNotExist:
            return Response({"error": "Purchase not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PurchaseSerializer(purchase)
        return Response(serializer.data, status=status.HTTP_200_OK)


class QueryPurchaseStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Orders - History"],
        summary="Query purchase status from provider",
        description="Re-query the VTU provider to get the latest status of a purchase. May trigger refund if confirmed failed.",
        responses={200: PurchaseSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    )
    def get(self, request, pk):
        try:
            purchase = Purchase.objects.get(pk=pk, user=request.user)
        except Purchase.DoesNotExist:
            return Response({"error": "Purchase not found."}, status=status.HTTP_404_NOT_FOUND)

        if not purchase.reference:
            return Response({"error": "No reference available for this purchase."}, status=status.HTTP_400_BAD_REQUEST)

        res = ProviderRouter.execute_with_fallback(purchase.purchase_type, "query_transaction", request_id=purchase.reference)
        
        if res.get('statuscode') == "200" or res.get('status') == "SUCCESS":
            purchase.status = "success"
            NotificationService.send_push(purchase.user, "Purchase Confirmed", f"Your {purchase.purchase_type} purchase is now successful.")
        elif res.get('status') == "FAILED":
            if purchase.status != "refunded":
                purchase.status = "refunded"
                fund_wallet(
                    purchase.user.id, 
                    purchase.amount, 
                    f"Refund: Query failed {purchase.purchase_type} purchase ({purchase.reference})",
                    initiator="system"
                )
                NotificationService.send_push(purchase.user, "Purchase Refunded", f"Your {purchase.purchase_type} purchase failed and has been refunded.")
        
        purchase.save()
        return Response(PurchaseSerializer(purchase).data, status=status.HTTP_200_OK)
