from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from wallet.models import VirtualAccount
from wallet.utils import fund_wallet
from .models import Deposit, Withdrawal
from .utils import PaystackGateway
from django.conf import settings
from django.contrib.auth import get_user_model
from summary.models import SiteConfig

import uuid
import logging
from rest_framework import status, permissions, generics, serializers
from rest_framework.response import Response
from .serializers import WithdrawalSerializer

from wallet.utils import debit_wallet

logger = logging.getLogger(__name__)


class PaymentWebhookView(APIView):
    """
    Endpoint to receive Paystack transaction / disbursement callbacks.
    """
    @method_decorator(csrf_exempt)  # since external POST
    def post(self, request, *args, **kwargs):
        client = PaystackGateway()
        is_verified = None
        is_verified = client.verify_webhook(request.body, request.headers['X-Paystack-Signature'])
    

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

            print(data)

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
                if created:
                    fund_wallet(deposit.user.id, amount_to_fund, "Wallet Top-Up", ref)
                    deposit.recieved = True
                    deposit.save()
                else:
                    if deposit.status != "SUCCESS":
                        deposit.status = "SUCCESS"
                        deposit.amount = amount
                        fund_wallet(deposit.user.id, amount_to_fund, "Wallet Top-Up", ref)
                        deposit.recieved = True
                        deposit.save()
                        
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

            User = get_user_model()
            customer = data['customer']
            user = get_object_or_404(User, email=customer['email'])

            if user == None:
                return HttpResponseBadRequest("User not found")
            

            
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
            
                # user account tier logic removed as requested
                pass

        elif event_type == "transfer.success":
            """Handle successful transfer webhook (single or bulk)."""
            transfer_code = data.get('transfer_code')
            reference = data.get('reference')

            if transfer_code:
                withdrawal = Withdrawal.objects.filter(transfer_code=transfer_code).first()
            elif reference:
                withdrawal = Withdrawal.objects.filter(reference=reference).first()
            else:
                withdrawal = None

            if withdrawal:
                withdrawal.transaction_status = "SUCCESS"
                if not withdrawal.transfer_code and transfer_code:
                    withdrawal.transfer_code = transfer_code
                withdrawal.save()
                logger.info(f"Transfer success for withdrawal {withdrawal.reference}")
            else:
                logger.warning(f"Transfer success webhook received but no matching withdrawal found. "
                             f"transfer_code={transfer_code}, reference={reference}")

        elif event_type == "transfer.failed":
            """Handle failed transfer webhook — refund user wallet."""
            transfer_code = data.get('transfer_code')
            reference = data.get('reference')

            if transfer_code:
                withdrawal = Withdrawal.objects.filter(transfer_code=transfer_code).first()
            elif reference:
                withdrawal = Withdrawal.objects.filter(reference=reference).first()
            else:
                withdrawal = None

            if withdrawal:
                withdrawal.transaction_status = "FAILED"
                withdrawal.status = "REJECTED"
                withdrawal.reason = data.get('reason', 'Transfer failed')
                withdrawal.save()

                # Refund the user's wallet
                try:
                    fund_wallet(
                        withdrawal.user.id,
                        withdrawal.amount,
                        f"Refund: Transfer failed for {withdrawal.reference}",
                    )
                    logger.info(f"Wallet refunded for failed withdrawal {withdrawal.reference}")
                except Exception as e:
                    logger.error(f"Failed to refund wallet for {withdrawal.reference}: {str(e)}")
            else:
                logger.warning(f"Transfer failed webhook received but no matching withdrawal found. "
                             f"transfer_code={transfer_code}, reference={reference}")

        elif event_type == "transfer.reversed":
            """Handle reversed transfer webhook — refund user wallet."""
            transfer_code = data.get('transfer_code')
            reference = data.get('reference')

            if transfer_code:
                withdrawal = Withdrawal.objects.filter(transfer_code=transfer_code).first()
            elif reference:
                withdrawal = Withdrawal.objects.filter(reference=reference).first()
            else:
                withdrawal = None

            if withdrawal and withdrawal.transaction_status != "FAILED":
                withdrawal.transaction_status = "FAILED"
                withdrawal.status = "REJECTED"
                withdrawal.reason = "Transfer reversed"
                withdrawal.save()

                try:
                    fund_wallet(
                        withdrawal.user.id,
                        withdrawal.amount,
                        f"Refund: Transfer reversed for {withdrawal.reference}",
                    )
                    logger.info(f"Wallet refunded for reversed withdrawal {withdrawal.reference}")
                except Exception as e:
                    logger.error(f"Failed to refund wallet for reversed {withdrawal.reference}: {str(e)}")

        return HttpResponse(status=200)
    



# Charge Configuration
class ChargesConfigView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        config = SiteConfig.objects.first()
        data = {
            "withdrawal_charge": float(config.withdrawal_charge) if config else 0.0,
            "deposit_charge": float(config.crediting_charge) if config else 0.0,
        }
        return Response(data, status=status.HTTP_200_OK)
