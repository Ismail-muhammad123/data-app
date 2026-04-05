import logging
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from wallet.models import VirtualAccount
from wallet.utils import fund_wallet, process_referral_reward
from payments.models import Deposit, Withdrawal
from payments.utils import PaystackGateway
from summary.models import SiteConfig

logger = logging.getLogger(__name__)

class PaymentWebhookView(APIView):
    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        client = PaystackGateway()
        if not client.verify_webhook(request.body, request.headers.get('X-Paystack-Signature')):
            return HttpResponseBadRequest("Invalid signature")
        event_type, data = request.data['event'], request.data['data']
        if event_type == "charge.success":
            ref, amount = data['reference'], float(data['amount']) / 100
            config = SiteConfig.objects.first()
            charge = config.crediting_charge if config else 0
            amount_to_fund = max(0, amount - float(charge))
            if data['authorization']['channel'] == 'dedicated_nuban':
                acc_num = data['authorization']['receiver_bank_account_number']
                va = VirtualAccount.objects.get(account_number=acc_num)
                deposit, created = Deposit.objects.get_or_create(reference=ref, defaults={"user":va.user, "amount":amount, "status":"SUCCESS", "payment_type":"CREDIT"})
                if created or deposit.status != "SUCCESS":
                    deposit.status, deposit.amount, deposit.recieved = "SUCCESS", amount, True; deposit.save()
                    fund_wallet(deposit.user.id, amount_to_fund, "Wallet Top-Up", ref)
                    process_referral_reward(deposit.user, trigger_event='credit', transaction_amount=amount)
            else:
                deposit = get_object_or_404(Deposit, reference=ref)
                if deposit.status != "SUCCESS":
                    deposit.status, deposit.amount = "SUCCESS", amount; deposit.save()
                    fund_wallet(deposit.user.id, amount_to_fund, reference=ref)
                    process_referral_reward(deposit.user, trigger_event='credit', transaction_amount=amount)
        elif event_type == "dedicatedaccount.assign.success":
            User = get_user_model()
            customer, acc = data['customer'], data['dedicated_account']
            user = get_object_or_404(User, email=customer['email'])
            if acc:
                VirtualAccount.objects.get_or_create(user=user, defaults={"account_number": acc["account_number"], "bank_name": acc["bank"]['name'], "account_name": acc['account_name'], "customer_email": customer["email"], "customer_name": customer["first_name"] + " " + customer["last_name"], "status": data.get("status", "ACTIVE").upper(), "account_reference": str(customer["id"])})
        elif event_type in ["transfer.success", "transfer.failed", "transfer.reversed"]:
            code, ref = data.get('transfer_code'), data.get('reference')
            withdrawal = Withdrawal.objects.filter(transfer_code=code).first() if code else Withdrawal.objects.filter(reference=ref).first()
            if withdrawal:
                if event_type == "transfer.success":
                    withdrawal.transaction_status = "SUCCESS"; withdrawal.save()
                else:
                    withdrawal.transaction_status, withdrawal.status = "FAILED", "REJECTED"
                    withdrawal.reason = data.get('reason', 'Transfer failed' if event_type == "transfer.failed" else 'Transfer reversed'); withdrawal.save()
                    fund_wallet(withdrawal.user.id, withdrawal.amount, f"Refund: {withdrawal.reason} for {withdrawal.reference}")
        return HttpResponse(status=200)
