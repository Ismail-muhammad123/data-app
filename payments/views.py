from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from wallet.models import VirtualAccount
from wallet.utils import fund_wallet
from .models import Deposit
from .utils import PaystackGateway
from django.conf import settings
from django.contrib.auth import get_user_model
from summary.models import SiteConfig

import uuid
from rest_framework import status, permissions, generics, serializers
from rest_framework.response import Response
from .models import Withdrawal
from .serializers import WithdrawalSerializer

from wallet.utils import debit_wallet


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
            amount_raw = data['amount']
            amount = float(amount_raw) / 100
            
            config = SiteConfig.objects.first()
            credit_charge = config.crediting_charge if config else 0
            amount_to_fund = max(0, amount - float(credit_charge))

            if data['authorization']['channel'] == 'dedicated_nuban':
                """Handle dedicated account (virtual account) payment webhook."""
                acc_num = data['authorization']['receiver_bank_account_number']
                virtual_account = VirtualAccount.objects.get(account_number=acc_num)
                deposit, created = Deposit.objects.get_or_create(
                    reference=ref,
                    defaults={
                        "user":virtual_account.user,
                        "amount":amount,
                        "status":"SUCCESS",
                        "payment_type":"CREDIT",
                    }
                )
                if not created:
                    if not deposit.status == "SUCCESS":
                        deposit.status = "SUCCESS"
                        deposit.amount = amount
                        deposit.save()
                        fund_wallet(deposit.user.id, amount_to_fund, "Wallet Top-Up", ref)
                else:
                    fund_wallet(deposit.user.id, amount_to_fund, "Wallet Top-Up", ref)
            else:
                """Handle other payment method webhook."""
                deposit = get_object_or_404(Deposit, reference=ref)
                if deposit.status != "SUCCESS":
                    deposit.status = "SUCCESS"
                    deposit.amount = amount
                    deposit.save()
                    fund_wallet(deposit.user.id, amount_to_fund, reference=ref)

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
    



class WithdrawalRequestView(generics.CreateAPIView):
    serializer_class = WithdrawalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        try:
            withdrawal_account = user.withdrawal_account
        except Exception:
            raise serializers.ValidationError({"error": "No withdrawal account set up. Please set up a withdrawal account first."})

        amount = serializer.validated_data['amount']
        
        try:
            # Debit wallet immediately to hold funds
            debit_wallet(user.id, amount, f"Withdrawal Request")
        except ValueError as e:
            raise serializers.ValidationError({"error": str(e)})

        serializer.save(
            user=user,
            reference=f"WTH-{uuid.uuid4().hex[:10].upper()}",
            bank_code=withdrawal_account.bank_code,
            account_number=withdrawal_account.account_number,
            account_name=withdrawal_account.account_name,
        )

class ChargesConfigView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        config = SiteConfig.objects.first()
        data = {
            "withdrawal_charge": float(config.withdrawal_charge) if config else 0.0,
            "deposit_charge": float(config.crediting_charge) if config else 0.0,
        }
        return Response(data, status=status.HTTP_200_OK)
