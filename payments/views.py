# payments/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from payments.utils import get_encrypted_key
from .models import Order, Payment
from django.conf import settings
import logging
import uuid
from seerbit.seerbitlib import SeerBit
import requests
logger = logging.getLogger(__name__)
SEERBIT_BASE_URL = "https://seerbitapi.com/api/v2"  # switch to sandbox if needed
    



# 1. Create a payment object and return Link

class PaymentInitView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, customer=request.user)
        reference = str(uuid.uuid4()) #f"{order.id}-{request.user.id}"

        encrypted_key = get_encrypted_key()

        payload = {
            "publicKey": settings.SEERBIT_PUBLIC_KEY,
            "amount": str(order.total_amount),
            "currency": "NGN",
            "country": "NG",
            "paymentReference": reference,
            "email": request.user.email,
            "fullName": request.user.full_name,
            "callbackUrl": settings.SEERBIT_CALLBACK_URL,
        }

        headers = {
            "Authorization": f"Bearer {encrypted_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(f"{SEERBIT_BASE_URL}/payments", json=payload, headers=headers)
        print(response.text)
        data = response.json()

        if response.status_code == 200 and data.get("status") == "SUCCESS":
            link = data["data"]["payments"]["redirectLink"]

            payment, _ = Payment.objects.update_or_create(
                order=order,
                defaults={
                    "user": request.user,
                    "transaction_ref": reference,
                    "amount": order.total_amount,
                    # "payment_url": link,
                }
            )

            return Response({"payment_url": link}, status=status.HTTP_200_OK)

        return Response(data, status=status.HTTP_400_BAD_REQUEST)
    




    
# 2. Verify payment with the ref in get param
class PaymentCallbackView(APIView):
    """
    Handles SeerBit callback and verifies payment
    """

    def post(self, request):
        reference = request.data.get("paymentReference")
        if not reference:
            return Response({"error": "paymentReference is required"}, status=status.HTTP_400_BAD_REQUEST)

        payment = get_object_or_404(Payment, transaction_ref=reference)

        # Fetch encrypted key
        try:
            encrypted_key = get_encrypted_key()
        except Exception as e:
            return Response({"error": f"Failed to get encrypted key: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Verify payment with SeerBit
        headers = {
            "Authorization": f"Bearer {encrypted_key}",
            "Content-Type": "application/json",
        }
        verify_url = f"{SEERBIT_BASE_URL}/payments/query/{reference}"

        response = requests.get(verify_url, headers=headers)
        data = response.json()

        if response.status_code == 200 and data.get("status") == "SUCCESS":
            payments_data = data["data"]["payments"]

            if payments_data.get("gatewayCode") == "00" and payments_data.get("reason") == "Successful":
                # ✅ Mark as successful
                payment.status = "success"
                payment.amount = payments_data.get("amount", payment.amount)
                payment.save()

                # Update related order
                payment.order.status = "paid"
                payment.order.save()

                return Response({
                    "message": "Payment successful",
                    "reference": reference,
                    "amount": payments_data.get("amount"),
                    "gatewayref": payments_data.get("gatewayref"),
                    "maskedPan": payments_data.get("maskedPan"),
                    "channelType": payments_data.get("channelType"),
                    "transactionTime": payments_data.get("transactionProcessedTime"),
                }, status=status.HTTP_200_OK)

        # ❌ If not successful
        payment.status = "FAILED"
        payment.save()
        return Response({"message": "Payment failed or not verified", "data": data}, status=status.HTTP_400_BAD_REQUEST)
    


# --- Payment endpoints (SeerBit flows) ---

# class MakePaymentAPIView(APIView):
#     """
#     Single endpoint to:
#     - Tokenize card & authorise (when card fields provided): returns authorizationCode or token
#     """
#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request):
#         ser = PaymentCreateSerializer(data=request.data)
#         ser.is_valid(raise_exception=True)
#         data = ser.validated_data
#         order = get_object_or_404(Order, pk=data["order_id"], customer=request.user)

#         # client = SeerbitClient()
#         if data.get("cardNumber") and data.get("expiryMonth") and data.get("expiryYear") and data.get("cvv") and data.get("pin"):
#             # First tokenize (amount can be 0.00 per docs if just creating token)
#             payment_reference = str(uuid.uuid4())
#             # tk_payload = {
#             #     "fullName": request.user.full_name,
#             #     "email": request.user.email,
#             #     "mobileNumber": request.user.phone,
#             #     "currency": "NGN",
#             #     "country": "NG",
#             #     "paymentType": "CARD",
#             #     "paymentReference": payment_reference,
#             #     "amount": float(order.total_amount),  # you may set "0.00" to only tokenize
#             #     # "productId": "",
#             #     # "productDescription": data["productDescription"],
#             #     "redirectUrl":"https://z9trade.com",
#             #     "cardNumber": data["cardNumber"],
#             #     "expiryMonth": data["expiryMonth"],
#             #     "expiryYear": data["expiryYear"],
#             #     "cvv": data.get("cvv", ""),
#             #     "pin": data.get("pin", "")
#             # }
#             try:
#                 # token_resp = client.tokenize_card(tk_payload)
#                 auth_token = authenticate()
#                 # print(auth_token)
                
#                 token_resp= card_authorize(auth_token, payment_reference,
#                     float(order.total_amount),
#                     request.user.full_name,
#                     request.user.email,
#                     request.user.phone,
#                     data["cardNumber"],
#                     data["expiryMonth"],     
#                     data["expiryYear"],
#                     data.get("cvv", ""),
#                     data.get("pin", "")
#                 )
#                 print(token_resp)
#                 # extract token path depends on SeerBit response; example:
#                 token = None
#                 try:
#                     token = token_resp["data"]["payments"]["card"]["token"]
#                 except Exception:
#                     token = token_resp.get("data", {}).get("token")  # fallback

#                 # If token exists and you want to immediately authorise (hold funds), call authorise:
#                 if token:
#                     # create Payment record with token
#                     p = Payment.objects.create(
#                         order=order,
#                         user=request.user,
#                         amount=order.total_amount,
#                         status="authorized" if token else "pending",
#                         token=token,
#                         transaction_ref=payment_reference,
#                         provider_response=token_resp
#                     )

#                     auth_payload = {
#                         "publicKey": settings.SEERBIT_PUBLIC_KEY,
#                         "amount": order.total_amount,
#                         "token": token,
#                         "paymentReference": payment_reference,
#                         "currency": "NGN",
#                         "country": "NG",
#                         "email": request.user.email,
#                         "fullName": request.user.full_name,
#                         # "productDescription": data["productDescription"],
#                     }
#                     # auth_resp = client.authorise_with_token(auth_payload)
#                     # parse auth_resp for authorizationCode (example structure)
#                     auth_code = None
#                     # auth_code = auth_resp.get("data", {}).get("authorizationCode") or auth_resp.get("data", {}).get("authorization_code")
#                     # p.provider_response = {"tokenize": token_resp, "authorise": auth_resp}
#                     if auth_code:
#                         p.authorization_code = auth_code
#                         p.status = "authorized"
#                     # you may inspect auth_resp to set success/failed appropriately
#                     p.save()
#                     return Response({"tokenize": token_resp, "authorise": auth_resp}, status=status.HTTP_200_OK)
#                 return Response({"detail": "Failed to verify card"}, status=400)
#             except Exception:
#                 logger.exception("seerbit tokenize/authorise failed")
#                 return Response({"detail": "Payment tokenization/authorisation failed"}, status=502)

#         return Response({"detail": "Invalid payment payload"}, status=400)



