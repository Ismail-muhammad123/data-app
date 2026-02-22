from django.db import models
from django.contrib.auth import get_user_model
from summary.views import get_api_wallet_balance, get_paystack_balance
from wallet.models import Wallet, WalletTransaction
from payments.models import Deposit, Withdrawal
from django.db.models import Q
from orders.models import DataService, DataVariation, AirtimeNetwork, Purchase

User = get_user_model()


class SummaryDashboard(Wallet):
    """
    A proxy model that doesn't store data — it aggregates statistics
    from other models across the system.
    """
    class Meta:
        proxy = True
        managed = False
        verbose_name = "Summary Dashboard"
        verbose_name_plural = "Summary Dashboard"

    @classmethod
    def summary(cls, start=None, end=None):
        
        wallets_transactions = WalletTransaction.objects.all()
        purchases = Purchase.objects.all()
        deposits = Deposit.objects.all()
        withdrawals = Withdrawal.objects.all()


        # USERS
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        verified_users = User.objects.filter(is_active=True, is_staff=False).count()
        unverified_users = User.objects.filter(is_active=False).count()

        # Date filtering
        if start:
            wallets_transactions = wallets_transactions.filter(timestamp__gte=start)
            purchases = purchases.filter(time__gte=start)
            deposits = deposits.filter(timestamp__gte=start)
            withdrawals = withdrawals.filter(created_at__gte=start)

        if end:
            wallets_transactions = wallets_transactions.filter(timestamp__lte=end)
            purchases = purchases.filter(time__lte=end)
            deposits = deposits.filter(timestamp__lte=end)
            withdrawals = withdrawals.filter(created_at__lte=end)

        total_wallet_balance = float(Wallet.objects.aggregate(models.Sum("balance"))["balance__sum"] or 0)
        wallet_debits = float(wallets_transactions.filter(Q(transaction_type="purchase") | Q(transaction_type="withdrawal")).aggregate(models.Sum("amount"))["amount__sum"] or 0)
        wallet_credits = float(wallets_transactions.filter(Q(transaction_type="deposit") | Q(transaction_type="reversal")).aggregate(models.Sum("amount"))["amount__sum"] or 0)

        # SALES SUMMARY
        total_purchases = float(purchases.aggregate(models.Sum("amount"))["amount__sum"] or 0)
        data_purchases = float(purchases.filter(purchase_type='data').aggregate(models.Sum("amount"))["amount__sum"] or 0)
        airtime_purchases = float(purchases.filter(purchase_type='airtime').aggregate(models.Sum("amount"))["amount__sum"] or 0)

        data_services = DataService.objects.all()
        airtime_networks = AirtimeNetwork.objects.all()

        airtime_sales = {}
        for i in airtime_networks:
            airtime_sales[i.service_name] = float(purchases.filter(airtime_service=i).aggregate(models.Sum("amount"))["amount__sum"] or 0)

        data_sales = {}
        for i in data_services:
            data_sales[i.service_name] = float(purchases.filter(data_variation__service=i).aggregate(models.Sum("amount"))["amount__sum"] or 0)

        # API WALLET BALANCE (VTU)
        vtu_balance = get_api_wallet_balance() or 0.0
        
        # PAYSTACK BALANCE (RESERVE)
        reserve_balance = get_paystack_balance() or 0.0

        # TOTAL SYSTEM FUNDS
        total_system_funds = vtu_balance + reserve_balance
        
        # DEPOSITS
        deposits_summary = { 
            "total_amount": float(deposits.filter(status="SUCCESS").aggregate(models.Sum("amount"))["amount__sum"] or 0),
            "pending_count": deposits.filter(status="PENDING").count(),
            "failed_count": deposits.filter(status="FAILED").count(),
            "success_count": deposits.filter(status="SUCCESS").count(),
        }

        # WITHDRAWALS
        withdrawals_summary = {
            "total_amount": float(withdrawals.filter(status="APPROVED").aggregate(models.Sum("amount"))["amount__sum"] or 0),
            "pending_count": withdrawals.filter(status="PENDING").count(),
            "approved_count": withdrawals.filter(status="APPROVED").count(),
            "rejected_count": withdrawals.filter(status="REJECTED").count(),
        }

        config = SiteConfig.objects.first()
        config_data = {
            "withdrawal_charge": float(config.withdrawal_charge) if config else 0,
            "crediting_charge": float(config.crediting_charge) if config else 0,
            "vtu_funding_bank_name": config.vtu_funding_bank_name if config else "",
            "vtu_funding_account_number": config.vtu_funding_account_number if config else "",
            "vtu_funding_account_name": config.vtu_funding_account_name if config else "",
        }

        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "verified": verified_users,
                "unverified": unverified_users,
            },
            "wallet": {
                "balance": total_wallet_balance,
                "debits": wallet_debits,
                "credits": wallet_credits,
            },
            "sales": {
                "total": total_purchases,
                "data": data_purchases,
                "airtime": airtime_purchases,
                "data_summary": data_sales,
                "airtime_summary": airtime_sales,
            },
            "deposits": deposits_summary,
            "withdrawals": withdrawals_summary,
            "api_wallet_balance": vtu_balance,
            "reserve_balance": reserve_balance,
            "total_system_funds": total_system_funds,
            "config": config_data,
        }

class SiteConfig(models.Model):
    withdrawal_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    crediting_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # VTU API Funding Details (The bank account to move money to for VTU funding)
    vtu_funding_bank_name = models.CharField(max_length=100, blank=True, null=True)
    vtu_funding_account_number = models.CharField(max_length=20, blank=True, null=True)
    vtu_funding_account_name = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"

    def __str__(self):
        return "Site Configuration"

    def save(self, *args, **kwargs):
        if not self.pk and SiteConfig.objects.exists():
            return 
        return super(SiteConfig, self).save(*args, **kwargs)


class SystemTransaction(models.Model):
    TRANSACTION_TYPES = [
        ("CASHOUT", "Cashout (Paystack to Bank)"),
        ("VTU_FUNDING", "VTU Wallet Funding"),
    ]
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    reference = models.CharField(max_length=100, unique=True)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} ({self.status})"

    class Meta:
        ordering = ["-created_at"]
