from decimal import Decimal
import requests
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import BankInformation
from payments.models import Deposit, Withdrawal
from .models import Wallet, WalletTransaction 
from .serializers import WalletSerializer, WalletTransactionSerializer
from django.conf import settings
import uuid

PAYSTACK_SECRET_KEY =  settings.PAYSTACK_SECRET_KEY 
PAYSTACK_PUBLIC_KEY = settings.PAYSTACK_PUBLIC_KEY 
PAYSTACK_BASE_URL = "https://api.paystack.co"
# CALLBACK_URL = settings.CALLBACK_URL

WITHDRAWAL_CHARGE = 20

headers = {
    "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
    "Content-Type": "application/json",
}




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




# class InitiateDepositView(APIView):

#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request):
#         user = request.user
#         amount = request.data.get("amount")

#         if not amount:
#             return Response({"error": "Amount is required"}, status=status.HTTP_400_BAD_REQUEST)

#         # Create a deposit record in your DB (status = pending)
#         # deposit = Deposit.objects.create(user=user, amount=amount, status="pending")


#         payload = {
#             "email": user.email,
#             "amount": int(amount) * 100,  # Paystack expects kobo
#             "metadata": {"user_id": user.id}
#             # "callback_url": CALLBACK_URL,
#         }

#         response = requests.post(f"{PAYSTACK_BASE_URL}/transaction/initialize", json=payload, headers=headers)

#         if response.status_code != 200:
#             return Response({"error": "Failed to initiate deposit"}, status=status.HTTP_400_BAD_REQUEST)

#         res_data = response.json()

#         # Save reference from Paystack into deposit record
#         Deposit.objects.create(
#             wallet=request.user.wallet,
#             amount=amount,
#             status="PENDING",
#             reference=res_data["data"]["reference"],
#         )

#         return Response(res_data, status=status.HTTP_201_CREATED)


# class InitiateWithdrawalView(APIView):
#     def post(self, request):
#         user = request.user
#         amount = request.data.get("amount")

#         try:
#             bank_info = BankInformation.objects.get(user=user)
#         except BankInformation.DoesNotExist:
#             return Response({"error": "Recieving Bank Information Not found for this user"},
#                             status=status.HTTP_400_BAD_REQUEST)

#         if not all([amount, bank_info, bank_info]):
#             return Response({"error": "Recieving Bank Information Not found for this user"},
#                             status=status.HTTP_400_BAD_REQUEST)

#         # Check wallet balance
#         if user.wallet.balance < amount + 20.0:
#             return Response({"error": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)

        
#         # Create withdrawal record in DB (status = pending)
#         withdrawal = Withdrawal.objects.create(
#             wallet=user.wallet, 
#             amount=amount, 
#             reference = str(uuid.uuid4()),
#             recieving_account_number=bank_info.account_number,
#             recieving_account_name=bank_info.account_name,
#             recieving_bank_name=bank_info.bank_name, 
#             status="PENDING",
#         )
        
#         # DEBIT
#         WalletTransaction.objects.create(
#             user=withdrawal.wallet.user,
#             wallet=withdrawal.wallet,
#             transaction_type="withdrawal",
#             # status="PENDING",
#             amount= withdrawal.amount,
#             balance_before=(withdrawal.wallet.balance + withdrawal.amount),
#             balance_after= withdrawal.wallet.balance,
#             description= "withdrawal",
#             reference= withdrawal.reference,
#         )
        
#         user.wallet.balance -= amount
#         user.wallet.save()

#         return Response({"message": "Withdrawal initiated, pending transfer"}, status=status.HTTP_201_CREATED)


# def initiate_transfer(withdrawal):
#     """
#     Initiates transfer to user's bank account using Paystack
#     withdrawal: Withdrawal instance or dict with account_number, bank_code, amount
#     """

#     payload = {
#         "source": "balance",
#         "reason": "Wallet withdrawal",
#         "amount": int(withdrawal.amount) * 100,  # kobo
#         "recipient": None,
#     }

#     # First create a transfer recipient
#     recipient_payload = {
#         "type": "nuban",
#         "name": f"{withdrawal.user.first_name} {withdrawal.user.last_name}",
#         "account_number": withdrawal.recieving_account_number,
#         "bank_code": withdrawal.recieving_bank_code,
#         "currency": "NGN"
#     }

#     r = requests.post(f"{PAYSTACK_BASE_URL}/transferrecipient", json=recipient_payload, headers=headers)
#     r_data = r.json()

#     if r.status_code != 200 or not r_data.get("status"):
#         # withdrawal.status = "failed"
#         # withdrawal.save()
#         return {"error": "Failed to create transfer recipient"}

#     recipient_code = r_data["data"]["recipient_code"]

#     payload["recipient"] = recipient_code

#     transfer_response = requests.post(f"{PAYSTACK_BASE_URL}/transfer", json=payload, headers=headers)
#     t_data = transfer_response.json()

#     if transfer_response.status_code == 200 and t_data.get("status"):
#         # withdrawal.reference = t_data["data"]["reference"]
#         # withdrawal.status = "processing"
#         # withdrawal.save()
#         return t_data
#     else:
#         # withdrawal.status = "failed"
#         # withdrawal.save()
#         return {"error": "Transfer initiation failed"}


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.conf import settings

from .models import Wallet
from payments.utils import initiate_card_payment, initiate_transfer

class FundWalletTransferView(APIView):
    """
    Initiate funding through Bank Transfer (Virtual Account).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            amount = request.data.get("amount")
            if not amount:
                return Response({"error": "Amount is required"}, status=status.HTTP_400_BAD_REQUEST)

            wallet = Wallet.objects.get(user=request.user)

            # Call Monnify util
            response = initiate_transfer(
                customer_name=request.user.get_full_name(),
                customer_email=request.user.email,
                customer_phone=request.user.phone,
                amount=amount,
                account_reference=f"wallet_{wallet.id}",
            )

            return Response({
                "message": "Transfer initiated successfully",
                "monnify_response": response
            }, status=status.HTTP_200_OK)

        except Wallet.DoesNotExist:
            return Response({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)


class FundWalletCardView(APIView):
    """
    Initiate funding through ATM Card.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            amount = request.data.get("amount")
            if not amount:
                return Response({"error": "Amount is required"}, status=status.HTTP_400_BAD_REQUEST)

            wallet = Wallet.objects.get(user=request.user)

            # Call Monnify util
            response = initiate_card_payment(
                customer_name=request.user.get_full_name(),
                customer_email=request.user.email,
                customer_phone=request.user.phone,
                amount=amount,
                payment_reference=f"wallet_{wallet.id}",
                redirect_url=settings.MONNIFY_CARD_REDIRECT_URL,  # e.g. frontend success/failure page
            )

            return Response({
                "message": "Card payment initiated successfully",
                "monnify_response": response
            }, status=status.HTTP_200_OK)

        except Wallet.DoesNotExist:
            return Response({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)
