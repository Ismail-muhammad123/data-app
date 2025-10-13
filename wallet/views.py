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




# ADMIN VIEWS
class WalletListView(generics.ListAPIView):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Wallet.objects.all()

class WalletDetailWithTransactionsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, wallet_id):
        try:
            wallet = Wallet.objects.get(pk=wallet_id)
            wallet_data = WalletSerializer(wallet).data
            transactions = wallet.transactions.all().order_by('-timestamp')
            transactions_data = WalletTransactionSerializer(transactions, many=True).data
            return Response({
                "wallet": wallet_data,
                "transactions": transactions_data
            }, status=status.HTTP_200_OK)
        except Wallet.DoesNotExist:
            return Response({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)

# class ManualCreditWalletView(APIView):
#     """
#     Admin manually credits a user's wallet.
#     """
#     permission_classes = [permissions.IsAdminUser]

#     def post(self, request):
#         wallet_id = request.data.get("wallet_id")
#         amount = request.data.get("amount")
#         description = request.data.get("description", "Manual credit")

#         if not wallet_id or not amount:
#             return Response({"error": "wallet_id and amount are required"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             wallet = Wallet.objects.get(pk=wallet_id)
#             wallet.balance += float(amount)
#             wallet.save()

#             # Log transaction
#             wallet.transactions.create(   
#                 user=wallet.user,
#                 wallet=wallet,
#                 transaction_type="deposit",
#                 amount=amount,
#                 balance_before=wallet.balance - float(amount),
#                 balance_after=wallet.balance,
#                 description=description,
#                 initiator='admin',
#                 initiated_by=request.user,
#                 timestamp=timezone.now()
#             )

#             return Response({"message": "Wallet credited successfully"}, status=status.HTTP_200_OK)
#         except Wallet.DoesNotExist:
#             return Response({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)


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

