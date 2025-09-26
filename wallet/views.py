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

# PAYSTACK_SECRET_KEY =  settings.PAYSTACK_SECRET_KEY 
# PAYSTACK_PUBLIC_KEY = settings.PAYSTACK_PUBLIC_KEY 
PAYSTACK_BASE_URL = "https://api.paystack.co"
# CALLBACK_URL = settings.CALLBACK_URL

# WITHDRAWAL_CHARGE = 20

# headers = {
#     "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
#     "Content-Type": "application/json",
# }




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


# FUND Wallet via transfer
class InitFundWalletViaTransferView(APIView):
    """
    Initiate funding through Bank Transfer (Virtual Account).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
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

            # init transaction
            res = monify_client.init_bank_transfer_payment(
                amount=amount, 
                customer_name=user.full_name, 
                customer_email=user.email, 
                payment_reference=ref, 
                payment_description="Wallet Top-up",
                meta_data={
                    "user_id": user.id,
                    "phone_number": user.phone_number,
                }
            )

            if res['requestSuccessful']:
                Payment.objects.create(
                    wallet=wallet,
                    amount=amount,
                    status="PENDING",
                    timestamp=timezone.now(),
                    reference=ref, 
                    payment_type="CREDIT",
                )

                return Response({
                    "message": "Transfer initiated successfully",
                    "monnify_response": res
                }, status=status.HTTP_200_OK)
            else: 
                return Response({
                    "message": "Transfer failed to be initialized",
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Wallet.DoesNotExist:
            return Response({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)

