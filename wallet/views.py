from decimal import Decimal
from django.db import transaction as db_transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
import uuid

from payments.models import Deposit, Withdrawal
from .models import (
    VirtualAccount, Wallet, TransferBeneficiary
)
from .serializers import (
    VirtualAccountSerializer, WalletSerializer, WalletTransactionSerializer,
    ResolveAccountSerializer, WalletTransferSerializer,
    TransferBeneficiarySerializer, BankTransferRequestSerializer,
    InitFundWalletRequestSerializer, VerifyRecipientRequestSerializer,
    WalletTransferResponseSerializer, BankTransferResponseSerializer,
    InitFundWalletResponseSerializer, VerifyRecipientResponseSerializer,
    ResolveAccountResponseSerializer, ErrorResponseSerializer,
    SuccessMessageSerializer, ChargesConfigResponseSerializer,
)
from .utils import fund_wallet, debit_wallet
from notifications.utils import NotificationService
from payments.utils import PaystackGateway

User = get_user_model()

# ──────────────────────────────────────────────
# Wallet Core Views
# ──────────────────────────────────────────────

class WalletDetailView(generics.RetrieveAPIView):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Wallet"],
        summary="Get wallet details",
        description="Retrieve the authenticated user's wallet balance.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        return wallet


class WalletTransactionListView(generics.ListAPIView):
    serializer_class = WalletTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Wallet"],
        summary="List wallet transactions",
        description="Retrieve a paginated list of all wallet transactions (credits and debits).",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        return wallet.transactions.all().order_by('-timestamp')


class WalletTransactionDetailView(generics.RetrieveAPIView):
    serializer_class = WalletTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Wallet"],
        summary="Get wallet transaction details",
        description="Retrieve details of a specific wallet transaction.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        return generics.get_object_or_404(wallet.transactions, pk=self.kwargs.get('pk'))

# ──────────────────────────────────────────────
# Withdrawal / Bank Transfer Views
# ──────────────────────────────────────────────

class InitiateBankTransferView(APIView):
    """Initiate a withdrawal/transfer to bank."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Wallet - Withdrawals"],
        summary="Withdraw to bank account",
        description="Initiate a bank withdrawal by providing bank details and transaction PIN.",
        request=BankTransferRequestSerializer,
        responses={201: BankTransferResponseSerializer, 400: ErrorResponseSerializer, 403: ErrorResponseSerializer}
    )
    def post(self, request):
        serializer = BankTransferRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        amount = serializer.validated_data['amount']
        pin = serializer.validated_data['transaction_pin']
        
        if not user.check_transaction_pin(pin):
            return Response({"error": "Invalid transaction PIN."}, status=status.HTTP_403_FORBIDDEN)
            
        bank_name = serializer.validated_data.get('bank_name')
        bank_code = serializer.validated_data.get('bank_code')
        account_number = serializer.validated_data.get('account_number')
        account_name = serializer.validated_data.get('account_name')
        
        reference = f"WTH-{uuid.uuid4().hex[:12].upper()}"
        
        with db_transaction.atomic():
            debit_wallet(
                user.id, 
                amount, 
                description=f"Withdrawal to {bank_name} ({account_number})",
                initiator="self"
            )
            
            Withdrawal.objects.create(
                user=user,
                amount=amount,
                bank_name=bank_name,
                bank_code=bank_code,
                account_number=account_number,
                account_name=account_name,
                reference=reference,
                status="PENDING"
            )
            
        NotificationService.send_push(user, "Withdrawal Initiated", f"Your withdrawal of {amount} has been initiated and is pending approval.")
        return Response({"message": "Withdrawal initiated successfully.", "reference": reference}, status=status.HTTP_201_CREATED)


# ──────────────────────────────────────────────
# Instant Wallet-to-Wallet Transfer
# ──────────────────────────────────────────────

class WalletTransferView(APIView):
    """Instant wallet-to-wallet transfer using phone number."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Wallet - P2P"],
        summary="Transfer to another user's wallet",
        description="Instantly send money to another user's wallet by their phone number. Requires transaction PIN.",
        request=WalletTransferSerializer,
        responses={200: WalletTransferResponseSerializer, 400: ErrorResponseSerializer, 401: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    )
    def post(self, request):
        serializer = WalletTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sender = request.user
        amount = serializer.validated_data['amount']
        recipient_phone = serializer.validated_data['recipient_phone']
        transaction_pin = serializer.validated_data['transaction_pin']
        description = serializer.validated_data.get('description', "Wallet Transfer")

        if not sender.check_transaction_pin(transaction_pin):
            return Response({"error": "Incorrect transaction PIN."}, status=status.HTTP_401_UNAUTHORIZED)

        search_phone = recipient_phone[1:] if recipient_phone.startswith('0') else recipient_phone
        try:
            recipient = User.objects.get(phone_number__icontains=search_phone)
        except User.DoesNotExist:
            return Response({"error": "Recipient not found."}, status=status.HTTP_404_NOT_FOUND)

        if sender == recipient:
            return Response({"error": "Cannot transfer to yourself."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with db_transaction.atomic():
                debit_wallet(sender.id, amount, description=f"Transfer to {recipient.phone_number}: {description}", initiator='self')
                fund_wallet(recipient.id, amount, description=f"Transfer from {sender.phone_number}: {description}", initiator='self')

            NotificationService.send_push(sender, "Transfer Successful", f"Sent N{amount} to {recipient.full_name or recipient.phone_number}.")
            NotificationService.send_push(recipient, "Credit Alert", f"Received N{amount} from {sender.full_name or sender.phone_number}.")
            
            return Response({"success": True, "message": f"Successfully transferred ₦{amount} to {recipient.full_name}."}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VerifyRecipientView(APIView):
    """Verify a user by phone number for P2P transfer."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Wallet - P2P"],
        summary="Verify P2P transfer recipient",
        description="Look up a user by phone number to verify their identity before initiating a wallet-to-wallet transfer. Returns recipient name, phone, and profile image.",
        parameters=[VerifyRecipientRequestSerializer],
        responses={200: VerifyRecipientResponseSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    )
    def get(self, request):
        phone_number = request.query_params.get('phone_number')
        if not phone_number:
            return Response({"error": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)

        search_phone = phone_number[1:] if phone_number.startswith('0') else phone_number
        try:
            recipient = User.objects.get(phone_number__icontains=search_phone)
            return Response({
                "full_name": recipient.full_name,
                "phone_number": recipient.phone_number,
                "profile_image": recipient.profile_image.url if recipient.profile_image else None,
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User with this phone number not found."}, status=status.HTTP_404_NOT_FOUND)


# ──────────────────────────────────────────────
# Transfer Beneficiaries
# ──────────────────────────────────────────────

@extend_schema(tags=["Wallet - Beneficiaries"])
class TransferBeneficiaryListCreateView(generics.ListCreateAPIView):
    """List and save bank transfer beneficiaries."""
    serializer_class = TransferBeneficiarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TransferBeneficiary.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=["Wallet - Beneficiaries"])
class TransferBeneficiaryDeleteView(generics.DestroyAPIView):
    """Delete a saved bank transfer beneficiary."""
    serializer_class = TransferBeneficiarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TransferBeneficiary.objects.filter(user=self.request.user)


# ──────────────────────────────────────────────
# Utility & Infrastructure Views
# ──────────────────────────────────────────────

class BankListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Wallet - Utilities"],
        summary="List all supported banks",
        description="Fetch the list of banks supported for withdrawals and account resolution."
    )
    def get(self, request):
        paystack = PaystackGateway(settings.PAYSTACK_SECRET_KEY)
        try:
            return Response(paystack.list_banks())
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ResolveAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Wallet - Utilities"],
        summary="Resolve bank account",
        description="Verify a bank account number and get the account holder's name.",
        request=ResolveAccountSerializer,
        responses={200: ResolveAccountResponseSerializer, 400: ErrorResponseSerializer}
    )
    def post(self, request):
        serializer = ResolveAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        paystack = PaystackGateway(settings.PAYSTACK_SECRET_KEY)
        try:
            return Response(paystack.resolve_account(serializer.validated_data['account_number'], serializer.validated_data['bank_code']))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VirtualAccountDetailView(generics.RetrieveAPIView):
    serializer_class = VirtualAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Wallet - Utilities"],
        summary="Get virtual account details",
        description="Retrieve the user's dedicated virtual bank account for funding.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        return VirtualAccount.objects.filter(user=self.request.user).first()


class InitFundWallet(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Wallet - Funding"],
        summary="Initiate wallet funding",
        description="Start a wallet deposit via Paystack payment. Returns a payment authorization URL.",
        request=InitFundWalletRequestSerializer,
        responses={200: InitFundWalletResponseSerializer, 400: ErrorResponseSerializer, 500: ErrorResponseSerializer}
    )
    def post(self, request):
        serializer = InitFundWalletRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]
        
        if Decimal(amount) < 100:
            return Response({"error": "Amount must be at least 100"}, status=status.HTTP_400_BAD_REQUEST)

        ref = f"DEP-{uuid.uuid4().hex[:12].upper()}"
        paystack = PaystackGateway(settings.PAYSTACK_SECRET_KEY)
        res = paystack.initialize_charge(email=request.user.email, amount=amount, reference=ref)
        
        if res['status']:
            Deposit.objects.create(user=request.user, amount=amount, status="PENDING", reference=ref, payment_type="CREDIT")
            return Response({"message": "Funding initiated", "response": res['data']})
        return Response({"error": "Funding failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
