from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
User = get_user_model()


class VirtualAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="virtual_account")
    account_number = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=100)
    account_name = models.CharField(max_length=200)
    account_reference = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_name = models.CharField(max_length=200)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.account_number}"


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name}'s wallet"


class WalletTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('purchase', 'Purchase'),
        ('reversal', 'Reversal')
    ]

    INITIATOR_CHOICES = [
        ("self", "Self"),
        ("admin", "Admin"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_transactions')
    wallet = models.ForeignKey(Wallet, on_delete=models.SET_NULL, null=True, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    deposit =models.OneToOneField("payments.Deposit", null=True, on_delete=models.SET_NULL, related_name="wallet_transaction")
    balance_before = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    initiator = models.CharField(max_length=6, choices=INITIATOR_CHOICES, default="self")
    initiated_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="initiated_transactions")
    reference = models.CharField(max_length=100, unique=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} on {self.timestamp.date()} for {self.user.email}"


class WithdrawalAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="withdrawal_account")
    bank_name = models.CharField(max_length=100)
    bank_code = models.CharField(max_length=10)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.phone_number} - {self.bank_name} - {self.account_number}"
