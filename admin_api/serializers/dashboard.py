from rest_framework import serializers
from summary.models import SiteConfig, ServiceCashback
from users.models import ReferralConfig, User

class ServiceCashbackSerializer(serializers.ModelSerializer):
    class Meta: model = ServiceCashback; fields = '__all__'

class AdminSiteConfigSerializer(serializers.ModelSerializer):
    cashbacks = serializers.SerializerMethodField()
    class Meta: model = SiteConfig; fields = '__all__'
    def get_cashbacks(self, obj): return ServiceCashbackSerializer(ServiceCashback.objects.all(), many=True).data

class AdminReferralConfigSerializer(serializers.ModelSerializer):
    class Meta: model = ReferralConfig; fields = '__all__'

class AdminReferralSerializer(serializers.ModelSerializer):
    referred_user_count = serializers.IntegerField(read_only=True); total_referral_earnings = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True); total_referral_transaction_value = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    class Meta: model = User; fields = ['id', 'phone_number', 'first_name', 'last_name', 'referral_code', 'referred_user_count', 'total_referral_earnings', 'total_referral_transaction_value']

class AdminDashboardStatsResponseSerializer(serializers.Serializer):
    class FinancialStatsSerializer(serializers.Serializer):
        total_deposits, total_withdrawals, total_transfers, paystack_balance, total_payouts = serializers.FloatField(), serializers.FloatField(), serializers.FloatField(), serializers.FloatField(), serializers.FloatField()
    class WalletsStatsSerializer(serializers.Serializer):
        total_balance, total_credits, total_debits = serializers.FloatField(), serializers.FloatField(), serializers.FloatField()
    class PurchaseStatsSerializer(serializers.Serializer):
        success_count, failed_count, pending_count = serializers.IntegerField(), serializers.IntegerField(), serializers.IntegerField(); total_volume = serializers.FloatField()
        class ServiceTotalSerializer(serializers.Serializer):
            total_amount, count, success, failed, pending = serializers.FloatField(), serializers.IntegerField(), serializers.IntegerField(), serializers.IntegerField(), serializers.IntegerField()
        totals_by_service = serializers.DictField(child=ServiceTotalSerializer()); total_commissions, total_profit = serializers.FloatField(), serializers.FloatField()
        class ProfitPeriodsSerializer(serializers.Serializer):
            today, weekly, monthly = serializers.FloatField(), serializers.FloatField(), serializers.FloatField()
        profit_periods = ProfitPeriodsSerializer()
    class UsersStatsSerializer(serializers.Serializer):
        total, active, inactive, agents, customers, admins, active_today = serializers.IntegerField(), serializers.IntegerField(), serializers.IntegerField(), serializers.IntegerField(), serializers.IntegerField(), serializers.IntegerField(), serializers.IntegerField()
    class VTUProviderStatsSerializer(serializers.Serializer):
        id, name, provider_key, is_active, balance, active_services, total_transactions, success_transactions, success_rate = serializers.IntegerField(), serializers.CharField(), serializers.CharField(), serializers.BooleanField(), serializers.FloatField(), serializers.IntegerField(), serializers.IntegerField(), serializers.IntegerField(), serializers.FloatField()
    class BusinessMetricsSerializer(serializers.Serializer):
        total_users, active_users_today, total_wallet_balance, total_transaction_volume = serializers.IntegerField(), serializers.IntegerField(), serializers.FloatField(), serializers.FloatField()
        class ProfitSerializer(serializers.Serializer):
            today, weekly, monthly = serializers.FloatField(), serializers.FloatField(), serializers.FloatField()
        profit = ProfitSerializer()
    class ServiceHealthSerializer(serializers.Serializer):
        network_status = serializers.DictField(child=serializers.CharField())
        class ProviderPerformanceSerializer(serializers.Serializer):
            name, is_active, success_rate, total_transactions = serializers.CharField(), serializers.BooleanField(), serializers.FloatField(), serializers.IntegerField()
        provider_performances = ProviderPerformanceSerializer(many=True); bill_system_success_rate = serializers.FloatField()
    class ProviderBalancesSerializer(serializers.Serializer):
        vtu, payment_gateway, sms = serializers.FloatField(), serializers.FloatField(), serializers.FloatField()
    class AlertsSerializer(serializers.Serializer):
        class FailedTransactionSerializer(serializers.Serializer):
            id, ref, type, amount, beneficiary, time = serializers.IntegerField(), serializers.CharField(), serializers.CharField(), serializers.FloatField(), serializers.CharField(), serializers.DateTimeField(); error = serializers.CharField(allow_null=True)
        failed_transactions = FailedTransactionSerializer(many=True); low_balance_warnings = serializers.ListField(child=serializers.CharField())
    class QuickActionsSerializer(serializers.Serializer):
        maintenance_mode = serializers.BooleanField(); services = serializers.DictField(child=serializers.BooleanField())
    class FinanceStatsSerializer(serializers.Serializer):
        class DepositStatsSerializer(serializers.Serializer):
            total_amount, success_count, pending_count, failed_count = serializers.FloatField(), serializers.IntegerField(), serializers.IntegerField(), serializers.IntegerField()
        class WithdrawalStatsSerializer(serializers.Serializer):
            total_amount, approved_count, pending_count, rejected_count = serializers.FloatField(), serializers.IntegerField(), serializers.IntegerField(), serializers.IntegerField()
        deposits, withdrawals = DepositStatsSerializer(), WithdrawalStatsSerializer()
    financial, wallets, purchases, users = FinancialStatsSerializer(), WalletsStatsSerializer(), PurchaseStatsSerializer(), UsersStatsSerializer(); vtu_providers, business_metrics, service_health, provider_balances, alerts, quick_actions, finances = VTUProviderStatsSerializer(many=True), BusinessMetricsSerializer(), ServiceHealthSerializer(), ProviderBalancesSerializer(), AlertsSerializer(), QuickActionsSerializer(), FinanceStatsSerializer()
