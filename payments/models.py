from django.db import models
from wallet.models import Wallet
from django.contrib.auth import get_user_model


User = get_user_model()

STATUS_OPTIONS = [
    ("PENDING", "Pending"),
    ("SUCCESS", "Success"),
    ("FAILED", "Failed"),
]

PAYMENT_TYPES = [
    ("DEBIT", "Debit"),
    ("CREDIT", "Credit"),
]

APPROVAL_STATUS_OPTIONS = [
    ("PENDING", "Pending"),
    ("APPROVED", "Approved"),
    ("REJECTED", "Rejected"),
]

class Deposit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_OPTIONS, default="PENDING")
    timestamp = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=100, unique=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default="CREDIT")
    recieved = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Deposit {self.amount} from {self.user}"

class Withdrawal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    bank_name = models.CharField(max_length=100)
    bank_code = models.CharField(max_length=10)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=APPROVAL_STATUS_OPTIONS, default="PENDING")
    transaction_status = models.CharField(max_length=10, choices=STATUS_OPTIONS, default="PENDING")
    reference = models.CharField(max_length=100, unique=True)
    transfer_code = models.CharField(max_length=100, null=True, blank=True)
    reason = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Withdrawal {self.amount} by {self.user.full_name}"


class TransferRecipient(models.Model):
    """
    Caches a Paystack transfer recipient so it can be reused
    for future transfers to the same withdrawal account.
    Keyed by WithdrawalAccount — if bank info changes, the old
    recipient is cascade-deleted and a new one is created.
    """
    withdrawal_account = models.OneToOneField(
        'wallet.WithdrawalAccount', on_delete=models.CASCADE,
        related_name='transfer_recipient'
    )
    recipient_code = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recipient {self.recipient_code} for {self.withdrawal_account}"