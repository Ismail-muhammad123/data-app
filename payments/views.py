from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from wallet.models import VirtualAccount
from wallet.utils import fund_wallet
from .models import Payment
from .utils import PaystackGateway
from django.conf import settings
from django.contrib.auth import get_user_model


# ADMIN Views
# class PaymentListView(generics.ListAPIView):
#     serializer_class = PaymentSerializer
#     permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

#     def get_queryset(self):
#         return Payment.objects.filter().order_by("-created_at")


# class PaymentCreateView(generics.CreateAPIView):
#     serializer_class = PaymentSerializer
#     permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

#     def create(self, request, *args, **kwargs):
#         data = request.data.copy()
#         data["user"] = request.user.id
#         data["reference"] = str(uuid.uuid4())  # auto-generate unique reference

#         serializer = self.get_serializer(data=data)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)


# class PaymentUpdateView(generics.UpdateAPIView):
#     queryset = Payment.objects.all()
#     serializer_class = PaymentSerializer
#     permission_classes = [permissions.IsAdminUser]  # only admin can update
#     lookup_field = "reference"  # update via reference instead of id



class PaymentWebhookView(APIView):
    """
    Endpoint to receive Paystack transaction / disbursement callbacks.
    """
    @method_decorator(csrf_exempt)  # since external POST
    def post(self, request, *args, **kwargs):
        # client = MonnifyClient()
        client = PaystackGateway(
            settings.PAYSTACK_SECRET_KEY
        )
        is_verified = None
        is_verified = client.verify_webhook(request.body, request.headers['X-Paystack-Signature'])
    

        # try:
        # except ValueError as e:
        #     
        if not is_verified:
            return HttpResponseBadRequest("Invalid signature")

        print("Webhook origin verified")

        event_type = request.data['event']
        data = request.data['data']


        # handle the different event types
        if event_type == "charge.success":
            """Handle successful charge webhook."""
            ref = data['reference']
            amount = data['amount']
            if data['authorization']['channel'] == 'dedicated_nuban':
                """Handle dedicated account (virtual account) payment webhook."""
                acc_num = data['authorization']['receiver_bank_account_number']
                virtual_account = VirtualAccount.objects.get(account_number=acc_num)
                payment, created = Payment.objects.get_or_create(
                    reference=ref,
                    defaults={
                        "user":virtual_account.user,
                        "amount":amount/100,
                        "status":"SUCCESS",
                        "payment_type":"CREDIT",
                    }
                )
                if not created:
                    if not payment.status == "SUCCESS":
                        payment.status = "SUCCESS"
                        payment.amount = amount/100
                        payment.save()
                        fund_wallet(payment.user.id, payment.amount, "Wallet Top-Up", ref)
                else:
                    fund_wallet(payment.user.id, payment.amount, "Wallet Top-Up", ref)
            else:
                """Handle other payment method webhook."""
                payment = get_object_or_404(Payment, reference=ref)
                amount = float(amount) / 100
                if payment.status != "SUCCESS":
                    payment.status = "SUCCESS"
                    payment.amount = amount
                    payment.save()
                    fund_wallet(payment.user.id, amount, reference=ref)

        elif event_type == "dedicatedaccount.assign.success":
            """Handle dedicated account assignment success webhook."""


            # {'event': 'dedicatedaccount.assign.success', 'data': {'customer': {'id': 325947837, 'first_name': 'Ismail', 'last_name': 'muhammmad', 'email': 'ismaeelmuhammad123@gmail.com', 'customer_code': 'CUS_icu86h5jyrlhgk2', 'phone': '+2348163351109', 'metadata': {}, 'risk_action': 'default', 'international_format_phone': '+2348163351109'}, 'dedicated_account': {'bank': {'name': 'Wema Bank', 'id': 20, 'slug': 'wema-bank'}, 'account_name': 'ASTARDATA/MUHAMMMAD ISMAIL', 'account_number': '9328428716', 'assigned': True, 'currency': 'NGN', 'metadata': None, 'active': True, 'id': 35159355, 'created_at': '2025-09-21T10:35:40.000Z', 'updated_at': '2025-12-21T08:57:48.000Z', 'assignment': {'assignee_id': 325947837, 'assignee_type': 'Customer', 'assigned_at': '2025-12-21T08:57:48.000Z', 'expired': False, 'expired_at': None, 'integration': 1622389, 'account_type': 'PAY-WITH-TRANSFER-RECURRING'}}}}


            User = get_user_model()
            customer = data['customer']
            user = get_object_or_404(User, email=customer['email'])

            if user == None:
                return HttpResponseBadRequest("User not found")
            
            if user.tier == 2:
                return HttpResponse("User already tier 2", status=200)
            
            acc= data['dedicated_account']
        
            if acc:
                account,_ = VirtualAccount.objects.get_or_create(
                    user=user,
                    defaults={
                        "account_number": acc["account_number"],
                        "bank_name": acc["bank"]['name'],
                        "account_name": acc['account_name'],
                        "customer_email": customer["email"],
                        "customer_name": customer["first_name"] + " " + customer["last_name"],
                        "status": data.get("status", "ACTIVE").upper(),
                        "account_reference": str(customer["id"]),
                    }
                )
            
                # upgrade user account tier to tier 2
                user.tier = 2
                user.save()
        # ... handle other events you care about

        return HttpResponse(status=200)
    

