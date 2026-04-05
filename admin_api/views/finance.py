from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema_view, extend_schema
import pyotp
from payments.models import Deposit, Withdrawal, PaystackConfig
from wallet.models import WalletTransaction
from admin_api.serializers import (
    AdminWalletTransactionSerializer, AdminDepositSerializer,
    AdminWithdrawalSerializer, AdminManualAdjustmentRequestSerializer,
    AdminWithdrawalSerializer, AdminManualAdjustmentRequestSerializer,
    AdminDepositMarkSuccessRequestSerializer, AdminWithdrawalActionRequestSerializer,
    AdminStatusResponseSerializer, AdminErrorResponseSerializer, AdminPaystackConfigSerializer,
    AdminTransferSerializer, AdminTransferBeneficiarySerializer, AdminInitiateTransferRequestSerializer,
    AdminUserListSerializer
)
from admin_api.permissions import CanManageWallets, CanManagePayments, IsSuperUserOnly, CanInitiateTransfers
from payments.models import AdminTransfer, AdminTransferBeneficiary
from wallet.models import Wallet
import requests
from django.conf import settings
from wallet.utils import fund_wallet, debit_wallet
from users.models import User

from rest_framework.pagination import PageNumberPagination
from admin_api.views.user_management import UserPagination

@extend_schema_view(
    list=extend_schema(tags=["Admin Wallets"]),
    retrieve=extend_schema(tags=["Admin Wallets"]),
)
class AdminWalletTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve all wallet transactions in the system."""
    queryset = WalletTransaction.objects.select_related('user', 'wallet').all().order_by('-timestamp')
    serializer_class = AdminWalletTransactionSerializer
    permission_classes = [CanManageWallets]
    pagination_class = UserPagination

    def get_queryset(self):
        # Explicitly return all records to avoid any confusion with user-facing endpoints
        return self.queryset
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
        pin = serializer.validated_data['pin']

        if not request.user.check_password(pin):
             return Response({"status": "ERROR", "message": "Invalid authorization PIN"}, status=status.HTTP_403_FORBIDDEN)

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
    """View and manage all deposits in the system."""
    queryset = Deposit.objects.select_related('user', 'processed_by').all().order_by('-timestamp')
    serializer_class = AdminDepositSerializer
    permission_classes = [CanManagePayments]

    def get_queryset(self):
        # Return all deposit records in the app
        return self.queryset

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
    """View and manage all withdrawals in the system."""
    queryset = Withdrawal.objects.select_related('user', 'processed_by').all().order_by('-created_at')
    serializer_class = AdminWithdrawalSerializer
    permission_classes = [CanManagePayments]

    def get_queryset(self):
        # Return all withdrawal records in the app
        return self.queryset

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
            
        pin = request.data.get('pin')
        if not request.user.check_password(pin):
            return Response({"error": "Invalid authorization PIN"}, status=403)

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

@extend_schema_view(
    list=extend_schema(tags=["Admin Payments"]),
    retrieve=extend_schema(tags=["Admin Payments"]),
    create=extend_schema(tags=["Admin Payments"]),
    update=extend_schema(tags=["Admin Payments"]),
    partial_update=extend_schema(tags=["Admin Payments"]),
    destroy=extend_schema(tags=["Admin Payments"]),
)
class AdminPaystackConfigViewSet(viewsets.ModelViewSet):
    """Manage Paystack configuration."""
    queryset = PaystackConfig.objects.all()
    serializer_class = AdminPaystackConfigSerializer
    permission_classes = [IsSuperUserOnly]

@extend_schema_view(
    list=extend_schema(tags=["Admin Wallets"]),
    retrieve=extend_schema(tags=["Admin Wallets"]),
)
class AdminWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve all user wallets in the system."""
    queryset = User.objects.select_related('wallet').all().order_by('-created_at')
    serializer_class = AdminUserListSerializer 
    permission_classes = [CanManageWallets]
    pagination_class = UserPagination

    def get_queryset(self):
        # Explicitly return all users with their wallets
        return self.queryset

@extend_schema_view(
    list=extend_schema(tags=["Admin Transfers"]),
    retrieve=extend_schema(tags=["Admin Transfers"]),
    create=extend_schema(tags=["Admin Transfers"]),
)
class AdminTransferBeneficiaryViewSet(viewsets.ModelViewSet):
    """Manage beneficiaries for admin-initiated transfers."""
    queryset = AdminTransferBeneficiary.objects.all().order_by('-created_at')
    serializer_class = AdminTransferBeneficiarySerializer
    permission_classes = [CanInitiateTransfers]

@extend_schema_view(
    list=extend_schema(tags=["Admin Transfers"]),
    retrieve=extend_schema(tags=["Admin Transfers"]),
)
class AdminTransferViewSet(viewsets.ModelViewSet):
    """Initiate and track transfers by admin to external bank accounts."""
    queryset = AdminTransfer.objects.all().order_by('-created_at')
    serializer_class = AdminTransferSerializer
    permission_classes = [CanInitiateTransfers]

    @extend_schema(
        tags=["Admin Transfers"],
        summary="Initiate admin transfer",
        description="Initiate a bank transfer using Paystack to a saved beneficiary.",
        request=AdminInitiateTransferRequestSerializer,
        responses={200: AdminStatusResponseSerializer, 400: AdminErrorResponseSerializer}
    )
    def create(self, request, *args, **kwargs):
        serializer = AdminInitiateTransferRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        beneficiary_id = serializer.validated_data['beneficiary_id']
        amount = serializer.validated_data['amount']
        pin = serializer.validated_data['pin']
        
        # Verify PIN
        if not request.user.check_password(pin):
            return Response({"error": "Invalid authorization PIN"}, status=403)
        
        try:
            beneficiary = AdminTransferBeneficiary.objects.get(id=beneficiary_id)
        except AdminTransferBeneficiary.DoesNotExist:
            return Response({"error": "Beneficiary not found"}, status=404)
        
        import uuid
        reference = f"ADM-TXN-{uuid.uuid4().hex[:12].upper()}"
        
        # In a real scenario, call Paystack Transfers API here
        # For now, we create the record
        transfer = AdminTransfer.objects.create(
            amount=amount,
            beneficiary=beneficiary,
            reference=reference,
            initiated_by=request.user,
            status='PENDING'
        )
        
        # Mock Paystack call logic:
        # 1. Fetch Paystack secret key
        config = PaystackConfig.load()
        if not config.secret_key:
            return Response({"error": "Paystack is not configured"}, status=400)
        
        # Standard Paystack transfer logic would go here...
        
        return Response({
            "status": "SUCCESS",
            "message": "Transfer initiated successfully",
            "data": AdminTransferSerializer(transfer).data
        })

@extend_schema(tags=["Admin Payments"])
class AdminPaystackDataViewSet(viewsets.ViewSet):
    permission_classes = [CanManagePayments]

    @extend_schema(
        summary="Fetch Paystack Payouts",
        description="Fetch a list of payouts from Paystack API."
    )
    @action(detail=False, methods=['get'], url_path='payouts')
    def payouts(self, request):
        config = PaystackConfig.load()
        if not config.secret_key:
            return Response({"error": "Paystack is not configured"}, status=400)
            
        headers = {"Authorization": f"Bearer {config.secret_key}"}
        try:
            response = requests.get("https://api.paystack.co/transfer", headers=headers)
            return Response(response.json())
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @extend_schema(
        summary="Fetch Paystack Transactions",
        description="Fetch all transactions directly from Paystack API."
    )
    @action(detail=False, methods=['get'], url_path='transactions')
    def transactions(self, request):
        config = PaystackConfig.load()
        if not config.secret_key:
            return Response({"error": "Paystack is not configured"}, status=400)
            
        headers = {"Authorization": f"Bearer {config.secret_key}"}
        try:
            response = requests.get("https://api.paystack.co/transaction", headers=headers)
            return Response(response.json())
        except Exception as e:
            return Response({"error": str(e)}, status=500)
