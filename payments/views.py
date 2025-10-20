from datetime import timezone
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics,permissions
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from payments.serializers import PaymentSerializer
from wallet.models import VirtualAccount
from wallet.utils import fund_wallet
from .models import Payment
from .utils import MonnifyClient
import uuid



# ADMIN Views
class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get_queryset(self):
        return Payment.objects.filter().order_by("-created_at")


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
        if event_type == "SUCCESSFUL_TRANSACTION":
            ref = data['paymentReference']
            # print("ref")
            # print(ref)
            amount = data['amountPaid']
            if data['product']['type'] == 'RESERVED_ACCOUNT':
                acc_num = data['destinationAccountInformation']['accountNumber']
                virtual_account = VirtualAccount.objects.get(account_number=acc_num)
                payment, created = Payment.objects.get_or_create(
                    reference=ref,
                    defaults={
                        "user":virtual_account.user,
                        "amount":amount,
                        "status":"SUCCESS",
                        "payment_type":"CREDIT",
                    }
                )
                if not created:
                    if not payment.status == "SUCCESS":
                        payment.status = "SUCCESS"
                        payment.amount = amount
                        payment.save()
                        fund_wallet(payment.user.id, payment.amount, "Wallet Top-Up", ref)
                else:
                    fund_wallet(payment.user.id, payment.amount, "Wallet Top-Up", ref)
            else:
                payment = get_object_or_404(Payment, reference=ref)
                if payment.status != "SUCCESS":
                    payment.status = "SUCCESS"
                    payment.amount = amount
                    payment.save()
        elif event_type == "SETTLEMENT_COMPLETION":
            # funds moved to your bank / wallet
            pass
        elif event_type == "FAILED_DISBURSEMENT":
            pass
        elif event_type == "SUCCESSFUL_DISBURSEMENT":
            pass
        # ... handle other events you care about

        return HttpResponse(status=200)
    

