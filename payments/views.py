from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.views import APIView
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView

from wallet.utils import fund_wallet
from .utils import MonnifyClient



from rest_framework.views import APIView

from .models import Payment
from .utils import MonnifyClient


# PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
# PAYSTACK_BASE_URL = "https://api.paystack.co"
# CALLBACK_URL = "" #request.build_absolute_uri("/api/deposit/callback/")

# WITHDRAWAL_CHARGE = 20

# headers = {
#     "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
#     "Content-Type": "application/json",
# }



# class PaymentWebhookView(APIView):
#     def post(self, request):
#         # Paystack will send events here

#         # TODO handle verification

#         payload = request.data
#         event = payload.get("event")

#         if event == "transfer.success":
#             reference = payload["data"]["reference"]
#             withdrawal = Withdrawal.objects.get(reference=reference)
#             withdrawal.status = "SUCCESS"
#             withdrawal.save()

#             trx = WalletTransaction.objects.get(reference=reference)
#             trx.status="SUCCESS"
#             trx.save()



#         elif event == "transfer.failed":
#             reference = payload["data"]["reference"]
#             withdrawal = Withdrawal.objects.get(reference=reference)
#             withdrawal.status = "FAILED"
#             withdrawal.save()

#             trx = WalletTransaction.objects.get(reference=reference)
#             trx.status="FAILED"
#             trx.save()

#             # REVRSAL
#             wallet = trx.wallet
#             wallet.amount += withdrawal.amount
#             wallet.save()

#             WalletTransaction.objects.create(
#                 user=withdrawal.user,
#                 wallet=withdrawal.user.wallet,
#                 transaction_type="reversal",
#                 status="SUCCESS",
#                 amount= withdrawal.amount,
#                 balance_before=(withdrawal.user.wallet.balance + withdrawal.amount),
#                 balance_after= withdrawal.user.wallet.balance,
#                 description= "withdrawal",
#                 reference= withdrawal.reference,
#             )

#         return Response({"message": "Webhook processed"}, status=status.HTTP_200_OK)


# class DepositCallbackView(APIView):
#     def get(self, request):
#         # Paystack will redirect to callback_url with reference in GET params
#         reference = request.GET.get("reference")
#         if not reference:
#             return render(request, "payments/payment_failed.html", status=400)

#         response = requests.get(f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}", headers=headers)

#         if response.status_code != 200:
#             return render(request, "payments/payment_failed.html", status=400)

#         res_data = response.json()
#         status_val = res_data["data"]["status"]

#         if status_val == "success":
#             deposit = Deposit.objects.get(reference=reference)
#             if deposit.status == "SUCCESS":
#                 return render(request, "payments/payment_success.html")
#             deposit = Deposit.objects.get(reference=reference)
#             deposit.status = "SUCCESS"
#             deposit.save()
#             deposit.wallet.balance += deposit.amount
#             deposit.wallet.save()

#             WalletTransaction.objects.create(
#                 user=deposit.wallet.user,
#                 wallet=deposit.wallet,
#                 transaction_type="deposit",
#                 amount= deposit.amount,
#                 balance_before=(deposit.wallet.balance - deposit.amount),
#                 balance_after= deposit.wallet.balance,
#                 description= "DEPOSIT",
#                 reference= deposit.reference,
#             )
#             return render(request, "payments/payment_success.html")
        
#         else:
#             deposit = Deposit.objects.get(reference=reference)
#             deposit.status = "FAILED"
#             deposit.save()
#             return render(request, "payment_failed.html")



# class FundWalletCardView(APIView):
#     """
#     Initiate funding through ATM Card.
#     """
#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request):
#         try:
#             amount = request.data.get("amount")
#             if not amount:
#                 return Response({"error": "Amount is required"}, status=status.HTTP_400_BAD_REQUEST)

#             wallet = Wallet.objects.get(user=request.user)

#             # Call Monnify util
#             response = initiate_card_payment(
#                 customer_name=request.user.get_full_name(),
#                 customer_email=request.user.email,
#                 customer_phone=request.user.phone,
#                 amount=amount,
#                 payment_reference=f"wallet_{wallet.id}",
#                 redirect_url=settings.MONNIFY_CARD_REDIRECT_URL,  # e.g. frontend success/failure page
#             )

#             return Response({
#                 "message": "Card payment initiated successfully",
#                 "monnify_response": response
#             }, status=status.HTTP_200_OK)

#         except Wallet.DoesNotExist:
#             return Response({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)


class PaymentWebhookView(APIView):
    """
    Endpoint to receive Monnify transaction / disbursement callbacks.
    """
    @method_decorator(csrf_exempt)  # since external POST
    def post(self, request, *args, **kwargs):
        client = MonnifyClient()
        try:
            event_type, data = client.handle_webhook_event(request.body, request.headers)
        except ValueError as e:
            return HttpResponseBadRequest("Invalid signature")

        # handle the different event types
        if event_type == "SUCCESSFUL_COLLECTION":
            ref = request['paymentReference']
            payment = get_object_or_404(Payment, reference=ref)
            if (payment.status is not "SUCCESSFUL"):
                payment.status= "SUCCESSFUL"
                wallet = payment.wallet
                fund_wallet(wallet.user.id, payment.amount, "Wallet Top-Up")
            pass
        elif event_type == "SETTLEMENT_COMPLETION":
            # funds moved to your bank / wallet
            pass
        elif event_type == "FAILED_DISBURSEMENT":
            pass
        elif event_type == "SUCCESSFUL_DISBURSEMENT":
            pass
        # ... handle other events you care about

        return HttpResponse(status=200)