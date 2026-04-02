from django.db import models
from django.contrib.auth import get_user_model
from summary.utils import get_api_wallet_balance, get_paystack_balance, get_termii_balance
from wallet.models import Wallet, WalletTransaction
from payments.models import Deposit, Withdrawal
from django.db.models import Q, Sum, F, Count, Avg
from django.utils import timezone
from datetime import timedelta
from orders.models import DataService, DataVariation, AirtimeNetwork, Purchase, VTUProviderConfig

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
        now = timezone.now()
        today = now.date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # USERS
        total_users = User.objects.count()
        active_users_today = User.objects.filter(last_login__date=today).count()
        active_users_total = User.objects.filter(is_active=True).count()
        verified_users = User.objects.filter(is_active=True, is_staff=False).count()
        unverified_users = User.objects.filter(is_active=False).count()

        # Date filtering for transactions
        filtered_purchases = Purchase.objects.filter(status="success")
        if start:
            filtered_purchases = filtered_purchases.filter(time__gte=start)
        if end:
            filtered_purchases = filtered_purchases.filter(time__lte=end)

        total_wallet_balance = float(Wallet.objects.aggregate(Sum("balance"))["balance__sum"] or 0)
        
        # SALES SUMMARY
        total_transaction_volume = float(filtered_purchases.aggregate(Sum("amount"))["amount__sum"] or 0)
        
        # PROFIT CALCULATION (Simplified: only for data which has cost_price)
        def calculate_profit(qs):
            # Only DataVariation has cost_price in the model
            data_profit = qs.filter(purchase_type='data', data_variation__isnull=False).annotate(
                p=F('amount') - F('data_variation__cost_price')
            ).aggregate(Sum('p'))['p__sum'] or 0
            # For others, we might need a different logic, but let's stick to this for now
            return float(data_profit)

        daily_profit = calculate_profit(Purchase.objects.filter(status="success", time__date=today))
        weekly_profit = calculate_profit(Purchase.objects.filter(status="success", time__gte=week_ago))
        monthly_profit = calculate_profit(Purchase.objects.filter(status="success", time__gte=month_ago))

        # SERVICE HEALTH INDICATORS
        networks = ['mtn', 'glo', 'airtel', '9mobile']
        health_indicators = {}
        for nw in networks:
            # Better logic: Filter by service name in the foreign key
            nw_purchases = Purchase.objects.filter(
                Q(airtime_service__service_name__icontains=nw) | 
                Q(data_variation__service__service_name__icontains=nw)
            ).order_by('-time')[:20]
            
            if not nw_purchases.exists():
                health_indicators[nw] = "🟢" # Assume green if no recent tx
            else:
                success_count = nw_purchases.filter(status="success").count()
                rate = success_count / nw_purchases.count()
                if rate >= 0.9: health_indicators[nw] = "🟢"
                elif rate >= 0.5: health_indicators[nw] = "🟡"
                else: health_indicators[nw] = "🔴"

        # PROVIDER PERFORMANCES
        provider_performances = VTUProviderConfig.objects.filter(is_active=True).annotate(
            total_tx=Count('purchases'),
            success_tx=Count('purchases', filter=Q(purchases__status='success')),
        )
        perf_data = []
        for p in provider_performances:
            rate = (p.success_tx / p.total_tx * 100) if p.total_tx > 0 else 100
            perf_data.append({
                "name": p.get_name_display(),
                "is_active": p.is_active,
                "success_rate": round(rate, 2),
                "total_transactions": p.total_tx
            })

        # Bill payment system health
        bill_services = ['electricity', 'tv', 'education', 'smile']
        bill_tx = Purchase.objects.filter(purchase_type__in=bill_services)
        bill_success_rate = 0
        if bill_tx.exists():
            bill_success_rate = (bill_tx.filter(status='success').count() / bill_tx.count()) * 100

        # PROVIDER BALANCES
        vtu_balance = get_api_wallet_balance() or 0.0
        reserve_balance = get_paystack_balance() or 0.0
        sms_balance = get_termii_balance() or 0.0

        # SMART ALERTS
        failed_transactions = Purchase.objects.filter(status="failed").order_by('-time')[:10]
        failed_data = [{
            "id": f.id,
            "ref": f.reference,
            "type": f.purchase_type,
            "amount": float(f.amount),
            "beneficiary": f.beneficiary,
            "time": f.time.isoformat(),
            "error": f.remarks
        } for f in failed_transactions]

        low_balance_alerts = []
        if vtu_balance < 5000: low_balance_alerts.append("Low VTU Provider Balance")
        if sms_balance < 1000: low_balance_alerts.append("Low SMS Provider Balance")

        # DEPOSITS & WITHDRAWALS
        deposits = Deposit.objects.all()
        withdrawals = Withdrawal.objects.all()
        if start:
            deposits = deposits.filter(timestamp__gte=start)
            withdrawals = withdrawals.filter(created_at__gte=start)
        if end:
            deposits = deposits.filter(timestamp__lte=end)
            withdrawals = withdrawals.filter(created_at__lte=end)

        deposits_summary = { 
            "total_amount": float(deposits.filter(status="SUCCESS").aggregate(Sum("amount"))["amount__sum"] or 0),
            "success_count": deposits.filter(status="SUCCESS").count(),
            "pending_count": deposits.filter(status="PENDING").count(),
            "failed_count": deposits.filter(status="FAILED").count(),
        }

        withdrawals_summary = {
            "total_amount": float(withdrawals.filter(status="APPROVED").aggregate(Sum("amount"))["amount__sum"] or 0),
            "approved_count": withdrawals.filter(status="APPROVED").count(),
            "pending_count": withdrawals.filter(status="PENDING").count(),
        }

        config = SiteConfig.objects.first()
        config_data = {
            "withdrawal_charge": float(config.withdrawal_charge) if config else 0,
            "crediting_charge": float(config.crediting_charge) if config else 0,
            "automatic_withdrawal": config.automatic_withdrawal if config else False,
            "withdrawals_enabled": config.withdrawals_enabled if config else True,
            "maintenance_mode": config.maintenance_mode if config else False,
            "services_status": {
                "airtime": config.airtime_active if config else True,
                "data": config.data_active if config else True,
                "tv": config.tv_active if config else True,
                "electricity": config.electricity_active if config else True,
                "education": config.education_active if config else True,
            }
        }

        return {
            "business_metrics": {
                "total_users": total_users,
                "active_users_today": active_users_today,
                "total_wallet_balance": total_wallet_balance,
                "total_transaction_volume": total_transaction_volume,
                "profit": {
                    "today": daily_profit,
                    "weekly": weekly_profit,
                    "monthly": monthly_profit,
                }
            },
            "service_health": {
                "network_status": health_indicators,
                "provider_performances": perf_data,
                "bill_system_success_rate": round(bill_success_rate, 2),
            },
            "provider_balances": {
                "vtu": vtu_balance,
                "payment_gateway": reserve_balance,
                "sms": sms_balance,
            },
            "alerts": {
                "failed_transactions": failed_data,
                "low_balance_warnings": low_balance_alerts,
            },
            "quick_actions": {
                "maintenance_mode": config_data["maintenance_mode"],
                "services": config_data["services_status"],
            },
            "finances": {
                "deposits": deposits_summary,
                "withdrawals": withdrawals_summary,
            }
        }

class SiteConfig(models.Model):
    withdrawal_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    crediting_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    automatic_withdrawal = models.BooleanField(default=False, help_text="If enabled, withdrawals will be processed automatically via Paystack.")
    withdrawals_enabled = models.BooleanField(default=True, help_text="Global toggle to enable or disable user withdrawals.")
    
    # VTU API Funding Details (The bank account to move money to for VTU funding)
    vtu_funding_bank_name = models.CharField(max_length=100, blank=True, null=True)
    vtu_funding_account_number = models.CharField(max_length=20, blank=True, null=True)
    vtu_funding_account_name = models.CharField(max_length=100, blank=True, null=True)

    # Global Automation settings
    auto_retry_enabled = models.BooleanField(default=True)
    auto_refund_enabled = models.BooleanField(default=True)
    notify_admin_on_failure = models.BooleanField(default=True)
    delayed_tx_detection_enabled = models.BooleanField(default=True)
    delayed_tx_timeout_minutes = models.PositiveIntegerField(default=15)

    # Maintenance and health
    maintenance_mode = models.BooleanField(default=False)
    airtime_active = models.BooleanField(default=True)
    data_active = models.BooleanField(default=True)
    tv_active = models.BooleanField(default=True)
    electricity_active = models.BooleanField(default=True)
    education_active = models.BooleanField(default=True)
    
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
