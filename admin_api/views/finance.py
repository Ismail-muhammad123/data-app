from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema_view, extend_schema
import pyotp
from payments.models import Deposit, Withdrawal
from wallet.models import WalletTransaction
from admin_api.serializers import (
    AdminWalletTransactionSerializer, AdminDepositSerializer,
    AdminWithdrawalSerializer, AdminManualAdjustmentRequestSerializer,
    AdminDepositMarkSuccessRequestSerializer, AdminWithdrawalActionRequestSerializer,
    AdminStatusResponseSerializer, AdminErrorResponseSerializer
)
from admin_api.permissions import CanManageWallets, CanManagePayments
from wallet.utils import fund_wallet, debit_wallet

@extend_schema_view(
    list=extend_schema(tags=["Admin Wallets"]),
    retrieve=extend_schema(tags=["Admin Wallets"]),
)
class AdminWalletTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WalletTransaction.objects.all().order_by('-timestamp')
    serializer_class = AdminWalletTransactionSerializer
    permission_classes = [CanManageWallets]
    filterset_fields = {
        'wallet': ['exact'],
        'user': ['exact'],
        'status': ['exact'],
        'transaction_type': ['exact'],
        'initiator': ['exact'],
        'initiated_by': ['exact'],
        'timestamp': ['exact', 'gte', 'lte'],
    }
    search_fields = ['reference', 'description', 'user__email', 'user__full_name']
    ordering_fields = ['timestamp', 'amount']

    @extend_schema(
        tags=["Admin Wallets"],
        summary="Manually adjust user wallet",
        description="Credit or debit a user's wallet with a specified amount and reason.",
        request=AdminManualAdjustmentRequestSerializer,
        responses={200: AdminStatusResponseSerializer}
    )
    @action(detail=False, methods=['post'], url_path='manual-adjustment')
    def manual_adjustment(self, request):
        serializer = AdminManualAdjustmentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = serializer.validated_data['user_id']
        amount = float(serializer.validated_data['amount'])
        adj_type = serializer.validated_data['type']
        reason = serializer.validated_data.get('reason', 'Admin Adjustment')

        if adj_type == 'credit':
            fund_wallet(user_id, amount, description=reason, initiator='admin', initiated_by=request.user)
        else:
            debit_wallet(user_id, amount, description=reason, initiator='admin', initiated_by=request.user)
        
        return Response({"status": "Wallet adjusted successfully"})

@extend_schema_view(
    list=extend_schema(tags=["Admin Payments"]),
    retrieve=extend_schema(tags=["Admin Payments"]),
    partial_update=extend_schema(tags=["Admin Payments"]),
)
class AdminDepositViewSet(viewsets.ModelViewSet):
    queryset = Deposit.objects.all().order_by('-timestamp')
    serializer_class = AdminDepositSerializer
    permission_classes = [CanManagePayments]

    @extend_schema(
        tags=["Admin Payments"],
        summary="Mark deposit as successful",
        description="Manually confirm a deposit and credit the user's wallet.",
        request=AdminDepositMarkSuccessRequestSerializer,
        responses={200: AdminStatusResponseSerializer, 400: AdminErrorResponseSerializer}
    )
    @action(detail=True, methods=['post'], url_path='mark-success')
    def mark_success(self, request, pk=None):
        deposit = self.get_object()
        if deposit.status == 'SUCCESS':
            return Response({"error": "Already marked successful"}, status=400)
        
        deposit.status = 'SUCCESS'
        deposit.recieved = True
        deposit.processed_by = request.user
        deposit.remarks = request.data.get('reason', 'Manually confirmed by Admin')
        deposit.save()
        
        fund_wallet(deposit.user.id, deposit.amount, description=f"Manual Deposit: {deposit.reference}", initiator='admin', initiated_by=request.user)
        return Response({"status": "SUCCESS", "message": "Deposit marked as success and wallet credited."})

@extend_schema_view(
    list=extend_schema(tags=["Admin Payments"]),
    retrieve=extend_schema(tags=["Admin Payments"]),
    partial_update=extend_schema(tags=["Admin Payments"]),
)
class AdminWithdrawalViewSet(viewsets.ModelViewSet):
    queryset = Withdrawal.objects.all().order_by('-created_at')
    serializer_class = AdminWithdrawalSerializer
    permission_classes = [CanManagePayments]

    @extend_schema(
        tags=["Admin Payments"],
        summary="Approve a withdrawal",
        description="Approve a pending withdrawal request. Requires admin 2FA OTP if enabled.",
        request=AdminWithdrawalActionRequestSerializer,
        responses={200: AdminStatusResponseSerializer, 400: AdminErrorResponseSerializer, 403: AdminErrorResponseSerializer}
    )
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        withdrawal = self.get_object()
        if withdrawal.status != 'PENDING':
            return Response({"error": f"Cannot approve withdrawal in {withdrawal.status} state"}, status=400)
            
        otp = request.data.get('otp')
        user = request.user
        if user.two_factor_secret:
            totp = pyotp.TOTP(user.two_factor_secret)
            if not otp or not totp.verify(otp):
                return Response({"error": "Invalid or missing OTP"}, status=403)

        withdrawal.status = 'APPROVED'
        withdrawal.transaction_status = 'SUCCESS'
        withdrawal.processed_by = request.user
        withdrawal.remarks = request.data.get('reason', 'Approved by Admin')
        withdrawal.save()
        
        return Response({"status": "SUCCESS", "message": "Withdrawal approved and transfer initiated."})

    @extend_schema(
        tags=["Admin Payments"],
        summary="Reject a withdrawal",
        description="Reject a pending withdrawal and refund the user's wallet.",
        request=AdminWithdrawalActionRequestSerializer,
        responses={200: AdminStatusResponseSerializer, 400: AdminErrorResponseSerializer}
    )
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        withdrawal = self.get_object()
        if withdrawal.status != 'PENDING':
             return Response({"error": f"Cannot reject withdrawal in {withdrawal.status} state"}, status=400)
             
        withdrawal.status = 'REJECTED'
        withdrawal.transaction_status = 'FAILED'
        withdrawal.processed_by = request.user
        withdrawal.remarks = request.data.get('reason', 'Rejected by Admin')
        withdrawal.save()
        
        fund_wallet(withdrawal.user.id, withdrawal.amount, description=f"Refund: Withdrawal rejected ({withdrawal.reference})", initiator='admin', initiated_by=request.user)
        
        return Response({"status": "REJECTED", "message": "Withdrawal rejected and funds refunded to user."})
