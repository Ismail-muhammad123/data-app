import uuid
from decimal import Decimal
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from payments.models import PaystackConfig, Deposit
from payments.utils import PaystackGateway
from wallet.serializers import (
    InitFundWalletRequestSerializer, InitFundWalletResponseSerializer, 
    ResolveAccountSerializer, ResolveAccountResponseSerializer, ErrorResponseSerializer
)

class InitFundWallet(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Wallet - Funding"], summary="Initiate wallet funding", request=InitFundWalletRequestSerializer, responses={200: InitFundWalletResponseSerializer})
    def post(self, request):
        serializer = InitFundWalletRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]
        if Decimal(amount) < 100: return Response({"error": "Min 100"}, status=400)
        ref = f"DEP-{uuid.uuid4().hex[:12].upper()}"
        config = PaystackConfig.objects.first()
        paystack = PaystackGateway(config.secret_key)
        res = paystack.initialize_charge(email=request.user.email, amount=amount, reference=ref)
        if res['status']:
            Deposit.objects.create(user=request.user, amount=amount, status="PENDING", reference=ref)
            return Response({"message": "Initiated", "response": res['data']})
        return Response({"error": "Failed"}, status=500)

class BankListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Wallet - Utilities"], summary="List supported banks")
    def get(self, request):
        config = PaystackConfig.objects.first()
        try: return Response(PaystackGateway(config.secret_key).list_banks())
        except Exception as e: return Response({"error": str(e)}, status=400)

class ResolveAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Wallet - Utilities"], summary="Resolve bank account", request=ResolveAccountSerializer, responses={200: ResolveAccountResponseSerializer})
    def post(self, request):
        serializer = ResolveAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        config = PaystackConfig.objects.first()
        try: return Response(PaystackGateway(config.secret_key).resolve_account(serializer.validated_data['account_number'], serializer.validated_data['bank_code']))
        except Exception as e: return Response({"error": str(e)}, status=400)
