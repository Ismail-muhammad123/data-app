from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from payments.models import Deposit
from .models import Wallet, WithdrawalAccount
from .serializers import (
    VirtualAccountSerializer, WalletSerializer, WalletTransactionSerializer,
    WithdrawalAccountSerializer, ResolveAccountSerializer
)
from django.conf import settings
import uuid
from payments.utils import MonnifyClient, PaystackGateway
from django.utils import timezone


# Wallet View
class WalletDetailView(generics.RetrieveAPIView):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        return wallet
    
# Get virtual account info
class VirtualAccountDetailView(generics.RetrieveAPIView):
    serializer_class = VirtualAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.virtual_account

# Bank List
class BankListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        paystack = PaystackGateway(settings.PAYSTACK_SECRET_KEY)
        try:
            banks = paystack.list_banks()
            return Response(banks, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Resolve Bank Account
class ResolveAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ResolveAccountSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        paystack = PaystackGateway(settings.PAYSTACK_SECRET_KEY)
        try:
            result = paystack.resolve_account(
                serializer.validated_data['account_number'],
                serializer.validated_data['bank_code']
            )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Withdrawal Account (Settlement Account)
class WithdrawalAccountDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = WithdrawalAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj, _ = WithdrawalAccount.objects.get_or_create(user=self.request.user)
        return obj
    
    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

# Transactions (list user's)
class WalletTransactionListView(generics.ListAPIView):
    serializer_class = WalletTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        return wallet.transactions.all().order_by('-timestamp')

class WalletTransactionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        try:
            transaction = wallet.transactions.get(pk=pk)
            data = WalletTransactionSerializer(transaction).data
            return Response(data, status=status.HTTP_200_OK)
        except wallet.transactions.model.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)

# FUND Wallet via transfer
class InitFundWallet(APIView):
    """
    Initiate funding through Bank Transfer (Virtual Account).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        method = request.data.get("method", "transfer")
        try:
            amount = request.data.get("amount")
            if not amount:
                return Response({"error": "Amount is required"}, status=status.HTTP_400_BAD_REQUEST)

            if int(amount) < 100:
                return Response({"error": "Amount has to bt NGN100 or more"}, status=status.HTTP_400_BAD_REQUEST)


            user = request.user
            wallet, _ = Wallet.objects.get_or_create(user=user)

            ref = str(uuid.uuid4())

            paystack_client = PaystackGateway(settings.PAYSTACK_SECRET_KEY)


            if method == "transfer":
                # init transaction


                res = paystack_client.initialize_charge(
                    email=user.email,
                    amount=amount,
                      reference=ref,
                    channels=['bank_transfer'],
                    metadata={
                        "phone_number": user.phone_number
                    }
                )
            else:
                res = paystack_client.initialize_charge(
                    email=user.email or "user1@gmail.com",
                    amount=amount,
                      reference=ref,
                    channels=['card','bank_transfer'],
                    metadata={
                        "phone_number": user.phone_number
                    }
                )
                

            print(res)

            if res['status']:
                Deposit.objects.create(
                    user=request.user,
                    amount=amount,
                    status="PENDING",
                    timestamp=timezone.now(),
                    reference=ref, 
                    payment_type="CREDIT",
                )

                return Response({
                    "message": "Wallet funding initiated successfully",
                    "response": res['data']
                }, status=status.HTTP_200_OK)
            else: 
                return Response({
                    "message": "Wallet funding failed to be initialized",
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Wallet.DoesNotExist:
            return Response({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)
