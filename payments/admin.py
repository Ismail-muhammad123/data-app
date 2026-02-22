from django.contrib import admin
from .models import Deposit, Withdrawal
from wallet.utils import debit_wallet, fund_wallet
from django.conf import settings
from .utils import PaystackGateway
from summary.models import SiteConfig
from django.contrib import messages

@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display =[
        "user", "amount", "status", "timestamp", "reference", "payment_type", "approval_status", ]
    list_filter = ["status", "payment_type", "approval_status", "timestamp"]
    search_fields = ["user__email", "user__phone_number", "reference"]
    readonly_fields = ["user", "amount", "status", "timestamp", "reference", "payment_type", "approval_status"]
    fieldsets = (
        ("Transaction Details", {
            "fields": ("user", "amount", "payment_type", "reference", "timestamp")
        }),
        ("Status & Approval", {
            "fields": ("status", "approval_status")
        }),
    )

    def has_add_permission(self, request):
        return False

@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ["user", "available_balance", "amount", "account_name", "account_number", "status", "transaction_status", "created_at"]
    list_filter = ["status", "transaction_status", "created_at"]
    search_fields = ["user__email", "user__phone_number", "reference", "account_number", "account_name"]
    readonly_fields = ["user", "amount", "account_name", "account_number", "bank_code", "reference", "status", "transaction_status", "transfer_code", "created_at"]
    fieldsets = (
        ("Request Information", {
            "fields": ("user", "amount", "reference", "created_at")
        }),
        ("Destination Account", {
            "fields": ("account_name", "account_number", "bank_code")
        }),
        ("Transaction Status", {
            "fields": ("status", "transaction_status", "transfer_code")
        }),
    )
    actions = ["approve_withdrawal", "reject_withdrawal"]


    def available_balance(self, obj):
        return obj.user.wallet.balance
    available_balance.short_description = "Available Balance"

    def approve_withdrawal(self, request, queryset):
        config = SiteConfig.objects.first()
        charge = config.withdrawal_charge if config else 0
        
        paystack = PaystackGateway(settings.PAYSTACK_SECRET_KEY)
        
        success_count = 0
        for withdrawal in queryset.filter(status="PENDING"):
            try:
                # Paystack payout (requested amount minus charge)
                # Note: Paystack amount is in kobo
                payout_amount_kobo = int((withdrawal.amount - charge) * 100)
                print("Payout amount kobo", payout_amount_kobo)
                if payout_amount_kobo < 10000:
                    withdrawal.status = "REJECTED"
                    withdrawal.reason = "Amount after charge is non-positive"
                    withdrawal.save()
                    request.message_user(request, f"Withdrawal {withdrawal.reference} rejected: Amount after charge is less than minimum withdrawal amount")
                    # Refund wallet since it was debited on request
                    fund_wallet(withdrawal.user.id, withdrawal.amount, f"Refund: {withdrawal.reference}")
                    continue

                response = paystack.make_payout(
                    name=withdrawal.account_name,
                    account_number=withdrawal.account_number,
                    bank_code=withdrawal.bank_code,
                    amount=payout_amount_kobo,
                    reason=f"Withdrawal {withdrawal.reference}"
                )

                print("Withdrawal response", response)
                
                withdrawal.status = "APPROVED"
                withdrawal.transaction_status = "SUCCESS"
                withdrawal.transfer_code = response.get("data", {}).get("transfer_code")
                withdrawal.save()
                success_count += 1
                
            except Exception as e:
                self.message_user(request, f"Error processing {withdrawal.reference}: {str(e)}", level=messages.ERROR)
        
        self.message_user(request, f"Successfully approved {success_count} withdrawal(s).")

    def reject_withdrawal(self, request, queryset):
        success_count = 0
        for withdrawal in queryset.filter(status="PENDING"):
            withdrawal.status = "REJECTED"
            withdrawal.save()
            # Refund wallet
            fund_wallet(withdrawal.user.id, withdrawal.amount, f"Refund: {withdrawal.reference}")
            success_count += 1
        self.message_user(request, f"Successfully rejected and refunded {success_count} withdrawal(s).")
    

