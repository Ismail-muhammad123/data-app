import uuid
from django.db import transaction as db_transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from wallet.models import TransferBeneficiary, User
from wallet.serializers import (
    BankTransferRequestSerializer, BankTransferResponseSerializer, WalletTransferSerializer, 
    WalletTransferResponseSerializer, VerifyRecipientRequestSerializer, VerifyRecipientResponseSerializer, 
    TransferBeneficiarySerializer, ErrorResponseSerializer
)
from wallet.utils import fund_wallet, debit_wallet
from notifications.utils import NotificationService
from payments.models import Withdrawal

class InitiateBankTransferView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Wallet - Withdrawals"], summary="Withdraw to bank", request=BankTransferRequestSerializer, responses={201: BankTransferResponseSerializer})
    def post(self, request):
        serializer = BankTransferRequestSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        user, amount, pin = request.user, serializer.validated_data['amount'], serializer.validated_data['transaction_pin']
        if not user.check_transaction_pin(pin): return Response({"error": "Invalid PIN"}, status=403)
        ref = f"WTH-{uuid.uuid4().hex[:12].upper()}"
        with db_transaction.atomic():
            debit_wallet(user.id, amount, description=f"Withdrawal to {serializer.validated_data['bank_name']}", initiator="self")
            Withdrawal.objects.create(user=user, amount=amount, bank_name=serializer.validated_data['bank_name'], bank_code=serializer.validated_data['bank_code'], account_number=serializer.validated_data['account_number'], account_name=serializer.validated_data['account_name'], reference=ref, status="PENDING")
        NotificationService.send_from_template(user, "withdrawal-initiated", {"amount": amount, "bank_name": serializer.validated_data['bank_name'], "reference": ref})
        return Response({"message": "Withdrawal initiated", "reference": ref}, status=201)

class WalletTransferView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Wallet - P2P"], summary="Transfer to another wallet", request=WalletTransferSerializer, responses={200: WalletTransferResponseSerializer})
    def post(self, request):
        serializer = WalletTransferSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        sender, amount, phone, pin = request.user, serializer.validated_data['amount'], serializer.validated_data['recipient_phone'], serializer.validated_data['transaction_pin']
        if not sender.check_transaction_pin(pin): return Response({"error": "Incorrect PIN"}, status=401)
        search_phone = phone[1:] if phone.startswith('0') else phone
        try: recipient = User.objects.get(phone_number__icontains=search_phone)
        except User.DoesNotExist: return Response({"error": "Recipient not found"}, status=404)
        if sender == recipient: return Response({"error": "Cannot transfer to yourself"}, status=400)
        with db_transaction.atomic():
            debit_wallet(sender.id, amount, description=f"Transfer to {recipient.phone_number}", initiator='self')
            fund_wallet(recipient.id, amount, description=f"Transfer from {sender.phone_number}", initiator='self')
        NotificationService.send_from_template(
            sender, 
            "wallet-transfer-sent", 
            {"amount": amount, "recipient": recipient.full_name or recipient.phone_number}
        )
        NotificationService.send_from_template(
            recipient, 
            "wallet-transfer-received", 
            {"amount": amount, "sender": sender.full_name or sender.phone_number, "balance": recipient.wallet.balance}
        )
        return Response({"success": True, "message": f"Transferred ₦{amount} to {recipient.full_name}."})

class VerifyRecipientView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Wallet - P2P"], summary="Verify recipient", parameters=[VerifyRecipientRequestSerializer], responses={200: VerifyRecipientResponseSerializer})
    def get(self, request):
        phone = request.query_params.get('phone_number')
        if not phone: return Response({"error": "Phone required"}, status=400)
        search_phone = phone[1:] if phone.startswith('0') else phone

        if search_phone == request.user.phone_number: return Response({"error": "Cannot transfer to yourself"}, status=400)
        try:
            r = User.objects.get(phone_number__icontains=search_phone)
            return Response({"full_name": r.full_name, "phone_number": r.phone_number, "profile_image": r.profile_image.url if r.profile_image else None})
        except User.DoesNotExist: return Response({"error": "Not found"}, status=404)

class TransferBeneficiaryListCreateView(generics.ListCreateAPIView):
    serializer_class = TransferBeneficiarySerializer; permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Wallet - Beneficiaries"])
    def get_queryset(self): return TransferBeneficiary.objects.filter(user=self.request.user)
    def perform_create(self, serializer): serializer.save(user=self.request.user)

class TransferBeneficiaryDeleteView(generics.DestroyAPIView):
    serializer_class = TransferBeneficiarySerializer; permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Wallet - Beneficiaries"])
    def get_queryset(self): return TransferBeneficiary.objects.filter(user=self.request.user)
