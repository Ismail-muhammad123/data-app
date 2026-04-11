from django.core.management.base import BaseCommand
from notifications.models import NotificationTemplate

class Command(BaseCommand):
    help = 'Seed default notification templates'

    def handle(self, *args, **options):
        templates = [
            {
                "slug": "wallet-funded",
                "title": "Wallet Funded Successfully",
                "body": "Your wallet has been credited with {amount}. New balance: {balance}. Ref: {reference}. Desc: {description}",
            },
            {
                "slug": "wallet-debited",
                "title": "Wallet Debited",
                "body": "Your wallet has been debited by {amount}. New balance: {balance}. Desc: {description}",
            },
            {
                "slug": "purchase-success",
                "title": "Purchase Successful",
                "body": "Your {service} purchase of {amount} to {beneficiary} was successful. Ref: {reference}",
            },
            {
                "slug": "purchase-failed",
                "title": "Purchase Failed",
                "body": "Your {service} purchase to {beneficiary} failed. Funds have been reversed. Ref: {reference}",
            },
            {
                "slug": "transaction-reversed",
                "title": "Transaction Reversed",
                "body": "Your {service} transaction of {amount} to {beneficiary} failed and has been reversed to your wallet. Ref: {reference}",
            },
            {
                "slug": "account-blocked",
                "title": "Account Blocked",
                "body": "Your account has been blocked. Reason: {reason}. Please contact support.",
            },
            {
                "slug": "account-unblocked",
                "title": "Account Reopened",
                "body": "Your account has been successfully unblocked. You can now resume your transactions.",
            },
            {
                "slug": "kyc-approved",
                "title": "KYC Approved",
                "body": "Congratulations! Your KYC verification has been approved. You now have full access to all features.",
            },
            {
                "slug": "kyc-rejected",
                "title": "KYC Rejected",
                "body": "Your KYC verification was rejected. Reason: {reason}. Please re-submit with correct information.",
            },
            {
                "slug": "transaction-pin-reset",
                "title": "Transaction PIN Reset",
                "body": "Your transaction PIN has been successfully reset by an administrator.",
            },
            {
                "slug": "login-pin-reset",
                "title": "Login PIN Reset",
                "body": "Your login PIN has been successfully reset by an administrator.",
            },
        ]

        created_count = 0
        updated_count = 0
        for data in templates:
            obj, created = NotificationTemplate.objects.get_or_create(
                slug=data['slug'],
                defaults={
                    "title": data['title'],
                    "body": data['body'],
                    "is_active": True,
                    "use_fcm": True,
                    "use_email": True,
                    "use_sms": False,
                    "use_whatsapp": False,
                }
            )
            if created:
                created_count += 1
            else:
                changed = False
                if obj.title != data['title']:
                    obj.title = data['title']
                    changed = True
                if obj.body != data['body']:
                    obj.body = data['body']
                    changed = True
                if not obj.is_active:
                    obj.is_active = True
                    changed = True
                if changed:
                    obj.save(update_fields=['title', 'body', 'is_active'])
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded templates. Created: {created_count}, Updated/Reactivated: {updated_count}.'
            )
        )
