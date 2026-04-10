from django.db import models

class AdminBeneficiary(models.Model):
    """
    Main account (Paystack/Flutterwave) recipients for fund replenishment (e.g. VTU Vendors).
    """
    name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=100)
    bank_code = models.CharField(max_length=20)
    account_number = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Admin Beneficiary"
        verbose_name_plural = "Admin Beneficiaries"

    def __str__(self):
        return f"{self.name} ({self.account_number})"


class AdminTransferLog(models.Model):
    """
    Tracking all transfers initiated from the admin account.
    """
    beneficiary = models.ForeignKey(AdminBeneficiary, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, default="PENDING") # SUCCESS, FAILED, PENDING
    initiated_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    gateway = models.CharField(max_length=20) # e.g. paystack, flutterwave
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Transfer of {self.amount} to {self.beneficiary.name}"


class AdminActionLog(models.Model):
    """
    Tracks administrative actions performed by staff members.
    """
    admin_user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='admin_action_logs')
    action_type = models.CharField(max_length=50) # e.g. "UPDATE_SITE_CONFIG", "CREDIT_WALLET", "REPLY_SUPPORT"
    target_model = models.CharField(max_length=100, blank=True, null=True)
    target_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Admin Action Log"
        verbose_name_plural = "Admin Action Logs"

    def __str__(self):
        return f"{self.admin_user.phone_number} - {self.action_type} - {self.created_at}"
