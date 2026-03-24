from django.contrib import admin
from .models import Deposit, Withdrawal, TransferRecipient
from wallet.utils import debit_wallet, fund_wallet
from django.conf import settings
from .utils import PaystackGateway
from summary.models import SiteConfig
from django.contrib import messages

import uuid
import logging

logger = logging.getLogger(__name__)


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display =[
        "user", "amount", "status", "timestamp", "reference", "payment_type", "recieved", ]
    list_filter = ["status", "payment_type", "recieved", "timestamp"]
    search_fields = ["user__email", "user__phone_number", "reference"]
    readonly_fields = ["user", "amount", "status", "timestamp", "reference", "payment_type", "recieved"]
    fieldsets = (
        ("Transaction Details", {
            "fields": ("user", "amount", "payment_type", "reference", "timestamp")
        }),
        ("Status & Approval", {
            "fields": ("status", "recieved")
        }),
    )

    def has_add_permission(self, request):
        return False


    actions = ["verify_payment"]

    def verify_payment(self, request, queryset):
        for deposit in queryset:
            if deposit.recieved == True:
                continue
            if deposit.status == "SUCCESS":
                try:
                    fund_wallet(deposit.user, deposit.amount, deposit.reference)
                    deposit.recieved = True
                    deposit.save()
                except Exception as e:
                    print(e)
                    self.message_user(request, f"Error processing {deposit.reference}: {str(e)}", level=messages.ERROR)
        messages.success(request, "Selected deposits approved successfully.")
    verify_payment.short_description = "Verify selected deposits"

    

@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ["user", "amount", "destination_account", "status", "transaction_status", "created_at"]
    list_filter = ["status", "transaction_status", "created_at"]
    search_fields = ["user__email", "user__phone_number", "reference", "account_number", "account_name"]
    readonly_fields = ["user", "amount", "account_name", "account_number", "bank_code", "reference", "status", "transaction_status", "transfer_code", "created_at"]
    fieldsets = (
        ("Request Information", {
            "fields": ("user", "amount", "reference",  "transfer_code", "created_at")
        }),
        ("Destination Account", {
            "fields": ("account_name", "account_number", "bank_code")
        }),
        ("Transaction Status", {
            "fields": ("status", "transaction_status",)
        }),
    )
    actions = ["approve_withdrawal", "approve_withdrawal_bulk", "reject_withdrawal"]

    def destination_account(self, obj):
        return f"{obj.account_name} | {obj.bank_name} - {obj.account_number}"
    destination_account.short_description = "Destination Account"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj = ...):
        return request.user.is_superuser

    def available_balance(self, obj):
        return obj.user.wallet.balance
    
    available_balance.short_description = "Available Balance"

    def _get_or_create_recipient(self, paystack, withdrawal):
        """
        Look up or create a Paystack transfer recipient for this withdrawal.
        Returns the recipient_code string.
        """
        # try:
        #     withdrawal_account = withdrawal.user.withdrawal_account
        # except Exception:
        #     withdrawal_account = None

        # # Try to find a cached recipient via the user's withdrawal account
        # if withdrawal_account:
        #     try:
        #         cached = withdrawal_account.transfer_recipient
        #         return cached.recipient_code
        #     except TransferRecipient.DoesNotExist:
        #         pass

        # Create a new recipient on Paystack
        response = paystack.create_recipient(
            name=withdrawal.account_name,
            account_number=withdrawal.account_number,
            bank_code=withdrawal.bank_code,
        )
        recipient_code = response["data"]["recipient_code"]

        # # Cache it if the user has a withdrawal account
        # if withdrawal_account:
        #     TransferRecipient.objects.update_or_create(
        #         withdrawal_account=withdrawal_account,
        #         defaults={"recipient_code": recipient_code},
        #     )

        return recipient_code

    # def approve_withdrawal(self, request, queryset):
    #     """Approve withdrawals one by one (single transfers)."""
    #     config = SiteConfig.objects.first()
    #     charge = config.withdrawal_charge if config else 0
        
    #     paystack = PaystackGateway(settings.PAYSTACK_SECRET_KEY)
        
    #     success_count = 0
    #     for withdrawal in queryset.filter(status="PENDING"):
    #         try:
    #             payout_amount_kobo = int((withdrawal.amount - charge) * 100)
    #             if payout_amount_kobo < 10000:
    #                 withdrawal.status = "REJECTED"
    #                 withdrawal.reason = "Amount after charge is non-positive"
    #                 withdrawal.save()
    #                 self.message_user(request, f"Withdrawal {withdrawal.reference} rejected: Amount after charge is less than minimum withdrawal amount")
    #                 fund_wallet(withdrawal.user.id, withdrawal.amount, f"Refund: {withdrawal.reference}")
    #                 continue

    #             recipient_code = self._get_or_create_recipient(paystack, withdrawal)

    #             response = paystack.make_payout(
    #                 name=withdrawal.account_name,
    #                 account_number=withdrawal.account_number,
    #                 bank_code=withdrawal.bank_code,
    #                 amount=payout_amount_kobo,
    #                 reason=f"Withdrawal {withdrawal.reference}",
    #                 recipient_code=recipient_code,
    #             )
                
    #             withdrawal.status = "APPROVED"
    #             withdrawal.transaction_status = "SUCCESS"
    #             withdrawal.transfer_code = response.get("data", {}).get("transfer_code")
    #             withdrawal.save()
    #             success_count += 1
                
    #         except Exception as e:
    #             self.message_user(request, f"Error processing {withdrawal.reference}: {str(e)}", level=messages.ERROR)
        
    #     self.message_user(request, f"Successfully approved {success_count} withdrawal(s).")
    # approve_withdrawal.short_description = "Approve selected withdrawals (single transfers)"

    def approve_withdrawal_bulk(self, request, queryset):
        """Approve multiple withdrawals via a single Paystack bulk transfer."""
        config = SiteConfig.objects.first()
        charge = config.withdrawal_charge if config else 0

        paystack = PaystackGateway(settings.PAYSTACK_SECRET_KEY)

        pending_withdrawals = queryset.filter(status="PENDING")
        transfers = []
        valid_withdrawals = []

        for withdrawal in pending_withdrawals:
            payout_amount_kobo = int((withdrawal.amount - charge) * 100)

            if payout_amount_kobo < 10000:
                withdrawal.status = "REJECTED"
                withdrawal.reason = "Amount after charge is below minimum"
                withdrawal.save()
                fund_wallet(withdrawal.user.id, withdrawal.amount, f"Refund: {withdrawal.reference}")
                self.message_user(
                    request,
                    f"Withdrawal {withdrawal.reference} rejected: amount too low.",
                    level=messages.WARNING,
                )
                continue

            try:
                recipient_code = self._get_or_create_recipient(paystack, withdrawal)
            except Exception as e:
                self.message_user(
                    request,
                    f"Failed to create recipient for {withdrawal.reference}: {str(e)}",
                    level=messages.ERROR,
                )
                continue

            transfers.append({
                "amount": payout_amount_kobo,
                "recipient": recipient_code,
                "reference": withdrawal.reference,
                "reason": f"Withdrawal for {withdrawal.user.phone_number}",
            })
            valid_withdrawals.append(withdrawal)

        if not transfers:
            self.message_user(request, "No valid withdrawals to process.", level=messages.WARNING)
            return

        try:
            response = paystack.initiate_bulk_transfer(transfers)
            logger.info(f"Bulk transfer response: {response}")

            # Mark as APPROVED but transaction_status stays PENDING
            # until confirmed via webhook (transfer.success / transfer.failed)
            for withdrawal in valid_withdrawals:
                withdrawal.status = "APPROVED"
                withdrawal.transaction_status = "PENDING"
                withdrawal.save()

            self.message_user(
                request,
                f"Bulk transfer initiated for {len(valid_withdrawals)} withdrawal(s). "
                f"Status will be updated via webhook.",
            )
        except Exception as e:
            logger.error(f"Bulk transfer failed: {str(e)}")
            self.message_user(
                request,
                f"Bulk transfer failed: {str(e)}",
                level=messages.ERROR,
            )
    approve_withdrawal_bulk.short_description = "Approve selected withdrawals (bulk transfer)"

    def reject_withdrawal(self, request, queryset):
        success_count = 0
        for withdrawal in queryset.filter(status="PENDING"):
            withdrawal.status = "REJECTED"
            withdrawal.save()
            # Refund wallet
            fund_wallet(withdrawal.user.id, withdrawal.amount, f"Refund: {withdrawal.reference}")
            success_count += 1
        self.message_user(request, f"Successfully rejected and refunded {success_count} withdrawal(s).")


# @admin.register(TransferRecipient)
# class TransferRecipientAdmin(admin.ModelAdmin):
#     list_display = ["withdrawal_account", "recipient_code", "created_at"]
#     search_fields = ["recipient_code", "withdrawal_account__account_number"]
#     readonly_fields = ["withdrawal_account", "recipient_code", "created_at"]

#     def has_add_permission(self, request):
#         return False

#     def has_change_permission(self, request, obj=None):
#         return False
