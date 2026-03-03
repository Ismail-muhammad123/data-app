from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from wallet.models import VirtualAccount
from wallet.utils import fund_wallet
from .models import Deposit, Withdrawal, TransferRecipient
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
        client = PaystackGateway(
            settings.PAYSTACK_SECRET_KEY
        )
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
    



class WithdrawalRequestView(generics.CreateAPIView):
    serializer_class = WithdrawalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        
        amount = serializer.validated_data['amount']
        account_name = serializer.validated_data['account_name']
        account_number = serializer.validated_data['account_number']
        bank_name = serializer.validated_data['bank_name']
        bank_code = serializer.validated_data['bank_code']
        reason = serializer.validated_data.get('reason', f"Withdrawal for {user.phone_number}")

        try:
            # Debit wallet immediately to hold funds
            debit_wallet(user.id, amount, "Withdrawal Request")
        except ValueError as e:
            raise serializers.ValidationError({"error": str(e)})

        withdrawal = serializer.save(
            user=user,
            reference=f"WTH-{uuid.uuid4().hex[:10].upper()}",
            # account_name, account_number, bank_name, bank_code, amount, and reason are already in validated_data
        )

        # Check if automatic withdrawal is enabled
        config = SiteConfig.objects.first()
        if config and config.automatic_withdrawal:
            try:
                charge = config.withdrawal_charge or 0
                payout_amount_kobo = int((amount - charge) * 100)
                
                # Minimum 100 Naira (10000 kobo) after charge
                if payout_amount_kobo >= 10000:
                    paystack_client = PaystackGateway(settings.PAYSTACK_SECRET_KEY)

                    # Try to look up cached recipient ONLY if it matches user's saved withdrawal account
                    recipient_code = None
                    withdrawal_account = None
                    try:
                        temp_withdrawal_account = user.withdrawal_account
                        if (temp_withdrawal_account.account_number == account_number and 
                            temp_withdrawal_account.bank_code == bank_code):
                            withdrawal_account = temp_withdrawal_account
                            try:
                                recipient_code = withdrawal_account.transfer_recipient.recipient_code
                            except Exception:
                                pass
                    except Exception:
                        pass
                    
                    response = paystack_client.make_payout(
                        name=account_name,
                        account_number=account_number,
                        bank_code=bank_code,
                        amount=payout_amount_kobo,
                        reason=reason,
                        recipient_code=recipient_code,
                    )
                    
                    if response.get('status'):
                        withdrawal.status = "APPROVED"
                        withdrawal.transaction_status = "SUCCESS"
                        if 'data' in response:
                            withdrawal.transfer_code = response['data'].get('transfer_code')

                            # Cache the recipient if it was newly created AND matches the user's saved account
                            if withdrawal_account and not recipient_code and response['data'].get('recipient_code'):
                                TransferRecipient.objects.update_or_create(
                                    withdrawal_account=withdrawal_account,
                                    defaults={"recipient_code": response['data']['recipient_code']},
                                )
                            # If no recipient_code in transfer response but we want to cache for future
                            elif withdrawal_account and not recipient_code:
                                try:
                                    r = paystack_client.create_recipient(
                                        name=account_name,
                                        account_number=account_number,
                                        bank_code=bank_code,
                                    )
                                    TransferRecipient.objects.update_or_create(
                                        withdrawal_account=withdrawal_account,
                                        defaults={"recipient_code": r['data']['recipient_code']},
                                    )
                                except Exception:
                                    pass  # Non-critical — caching failed but transfer succeeded

                        withdrawal.save()
                else:
                    logger.warning(f"Automatic withdrawal skipped for {withdrawal.reference}: Amount after charge (₦{payout_amount_kobo/100}) is below minimum ₦100.")
                    
            except Exception as e:
                logger.error(f"Automatic withdrawal failed for {withdrawal.reference}: {str(e)}")
                # We leave it as PENDING for manual review/processing

class ChargesConfigView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        config = SiteConfig.objects.first()
        data = {
            "withdrawal_charge": float(config.withdrawal_charge) if config else 0.0,
            "deposit_charge": float(config.crediting_charge) if config else 0.0,
        }
        return Response(data, status=status.HTTP_200_OK)
