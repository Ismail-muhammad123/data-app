from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.models import Payment
from .models import Wallet 
from .serializers import WalletSerializer, WalletTransactionSerializer
from django.conf import settings
import uuid
from payments.utils import MonnifyClient
from django.utils import timezone



from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import VirtualAccount
from .serializers import VirtualAccountSerializer
from payments.utils import MonnifyClient

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_virtual_account(request):
    user = request.user

    # Check if KYC and profile are complete
    if user.tier == 2:
        return Response({"error": "Account is already a tier two account"})


    if not user.full_name != "" and (user.email or '') != "" and (user.nin or '') != "" and (user.bvn or '') != "":
        return Response({"error": "User profile information is incomplete."}, status=400)

    # Prevent duplicate accounts
    if VirtualAccount.objects.filter(user=user).exists():
        return Response({"error": "Virtual account already exists."}, status=400)

    try:
        client = MonnifyClient()
        monnify_data = client.create_reserved_account(user)
        account = VirtualAccount.objects.create(
            user=user,
            account_number=monnify_data["accountNumber"],
            bank_name=monnify_data["bankName"],
            account_reference=monnify_data["accountReference"],
            customer_email=monnify_data["customerEmail"],
            customer_name=monnify_data["customerName"],
            status=monnify_data.get("status", "ACTIVE"),
        )
        
        # upgrade user account tier to tier 2
        user.tier = 2
        user.save()

        serializer = VirtualAccountSerializer(account)
        return Response(serializer.data, status=201)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# Wallet View
class WalletDetailView(generics.RetrieveAPIView):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        return wallet

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
            wallet = Wallet.objects.get(user=user)

            ref = str(uuid.uuid4())

            monify_client = MonnifyClient()


            if method == "transfer":
                # init transaction
                res = monify_client.init_bank_transfer_payment(
                    amount=amount, 
                    customer_name=user.full_name, 
                    customer_email=user.email, 
                    payment_reference=ref, 
                    payment_description="Wallet Top-up",
                    meta_data={
                        "phone_number": user.phone_number,
                    }
                )
            else:
                res = monify_client.init_card_payment(
                    amount=amount, 
                    customer_name=user.full_name, 
                    customer_email=user.email, 
                    payment_reference=ref, 
                    payment_description="Wallet Top-up",
                    meta_data={
                        "phone_number": user.phone_number,
                    }
                )

            if res['requestSuccessful']:
                Payment.objects.create(
                    user=request.user,
                    amount=amount,
                    status="PENDING",
                    timestamp=timezone.now(),
                    reference=ref, 
                    payment_type="CREDIT",
                )

                return Response({
                    "message": "Wallet funding initiated successfully",
                    "monnify_response": res
                }, status=status.HTTP_200_OK)
            else: 
                return Response({
                    "message": "Wallet funding failed to be initialized",
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Wallet.DoesNotExist:
            return Response({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)

