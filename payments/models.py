from django.db import models
from django.conf import settings
from orders.models import Order 


class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("authorized", "Authorized"),
        ("captured", "Captured"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, related_name="payments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=50, default="seerbit")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    # artifacts from SeerBit:
    token = models.CharField(max_length=255, blank=True, null=True)              # tk_... card token
    authorization_code = models.CharField(max_length=255, blank=True, null=True) # auth code returned upon charge/authorized
    transaction_ref = models.CharField(max_length=255, blank=True, null=True)    # paymentReference
    provider_response = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id} - {self.order} - {self.status}"