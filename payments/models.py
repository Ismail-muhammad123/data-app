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

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_OPTIONS, default="PENDING")
    timestamp = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=100, unique=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_OPTIONS, default="PENDING")
    # recieving_account_number = models.CharField(max_length=15)
    # recieving_account_name = models.CharField(max_length=200)
    # recieving_bank_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.payment_type} {self.amount} from {self.user}"
   