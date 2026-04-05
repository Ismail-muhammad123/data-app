from rest_framework import serializers
from summary.models import SiteConfig, ServiceCashback
from users.models import ReferralConfig, User
from drf_spectacular.utils import extend_schema_field

class ServiceCashbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCashback
        fields = '__all__'

class AdminSiteConfigSerializer(serializers.ModelSerializer):
    cashbacks = serializers.SerializerMethodField()

    class Meta:
        model = SiteConfig
        fields = '__all__'

    @extend_schema_field(ServiceCashbackSerializer(many=True))
    def get_cashbacks(self, obj):
        return ServiceCashbackSerializer(ServiceCashback.objects.all(), many=True).data

class AdminReferralConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralConfig
        fields = '__all__'

class AdminReferralSerializer(serializers.ModelSerializer):
    referred_user_count = serializers.IntegerField(read_only=True)
    total_referral_earnings = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_referral_transaction_value = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'first_name', 'last_name', 'referral_code', 
            'referred_user_count', 'total_referral_earnings', 'total_referral_transaction_value'
        ]

class AdminDashboardStatsResponseSerializer(serializers.Serializer):
    class FinancialStatsSerializer(serializers.Serializer):
        total_deposits = serializers.FloatField()
        total_withdrawals = serializers.FloatField()
        total_transfers = serializers.FloatField()
        paystack_balance = serializers.FloatField()
        total_payouts = serializers.FloatField()

    class WalletsStatsSerializer(serializers.Serializer):
        total_balance = serializers.FloatField()
        total_credits = serializers.FloatField()
        total_debits = serializers.FloatField()

    class PurchaseStatsSerializer(serializers.Serializer):
        success_count = serializers.IntegerField()
        failed_count = serializers.IntegerField()
        pending_count = serializers.IntegerField()
        total_volume = serializers.FloatField()

        class ServiceTotalSerializer(serializers.Serializer):
            total_amount = serializers.FloatField()
            count = serializers.IntegerField()
            success = serializers.IntegerField()
            failed = serializers.IntegerField()
            pending = serializers.IntegerField()

        totals_by_service = serializers.DictField(child=ServiceTotalSerializer())
        total_commissions = serializers.FloatField()
        total_profit = serializers.FloatField()

        class ProfitPeriodsSerializer(serializers.Serializer):
            today = serializers.FloatField()
            weekly = serializers.FloatField()
            monthly = serializers.FloatField()

        profit_periods = ProfitPeriodsSerializer()

    class UsersStatsSerializer(serializers.Serializer):
        total = serializers.IntegerField()
        active = serializers.IntegerField()
        inactive = serializers.IntegerField()
        agents = serializers.IntegerField()
        customers = serializers.IntegerField()
        admins = serializers.IntegerField()
        active_today = serializers.IntegerField()

    class VTUProviderStatsSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        name = serializers.CharField()
        provider_key = serializers.CharField()
        is_active = serializers.BooleanField()
        balance = serializers.FloatField()
        active_services = serializers.IntegerField()
        total_transactions = serializers.IntegerField()
        success_transactions = serializers.IntegerField()
        success_rate = serializers.FloatField()

    class BusinessMetricsSerializer(serializers.Serializer):
        total_users = serializers.IntegerField()
        active_users_today = serializers.IntegerField()
        total_wallet_balance = serializers.FloatField()
        total_transaction_volume = serializers.FloatField()

        class ProfitSerializer(serializers.Serializer):
            today = serializers.FloatField()
            weekly = serializers.FloatField()
            monthly = serializers.FloatField()

        profit = ProfitSerializer()

    class ServiceHealthSerializer(serializers.Serializer):
        network_status = serializers.DictField(child=serializers.CharField())

        class ProviderPerformanceSerializer(serializers.Serializer):
            name = serializers.CharField()
            is_active = serializers.BooleanField()
            success_rate = serializers.FloatField()
            total_transactions = serializers.IntegerField()

        provider_performances = ProviderPerformanceSerializer(many=True)
        bill_system_success_rate = serializers.FloatField()

    class ProviderBalancesSerializer(serializers.Serializer):
        vtu = serializers.FloatField()
        payment_gateway = serializers.FloatField()
        sms = serializers.FloatField()

    class AlertsSerializer(serializers.Serializer):
        class FailedTransactionSerializer(serializers.Serializer):
            id = serializers.IntegerField()
            ref = serializers.CharField()
            type = serializers.CharField()
            amount = serializers.FloatField()
            beneficiary = serializers.CharField()
            time = serializers.DateTimeField()
            error = serializers.CharField(allow_null=True)

        failed_transactions = FailedTransactionSerializer(many=True)
        low_balance_warnings = serializers.ListField(child=serializers.CharField())

    class QuickActionsSerializer(serializers.Serializer):
        maintenance_mode = serializers.BooleanField()
        services = serializers.DictField(child=serializers.BooleanField())

    class FinanceStatsSerializer(serializers.Serializer):
        class DepositStatsSerializer(serializers.Serializer):
            total_amount = serializers.FloatField()
            success_count = serializers.IntegerField()
            pending_count = serializers.IntegerField()
            failed_count = serializers.IntegerField()

        class WithdrawalStatsSerializer(serializers.Serializer):
            total_amount = serializers.FloatField()
            approved_count = serializers.IntegerField()
            pending_count = serializers.IntegerField()
            rejected_count = serializers.IntegerField()

        deposits = DepositStatsSerializer()
        withdrawals = WithdrawalStatsSerializer()

    financial = FinancialStatsSerializer()
    wallets = WalletsStatsSerializer()
    purchases = PurchaseStatsSerializer()
    users = UsersStatsSerializer()
    vtu_providers = VTUProviderStatsSerializer(many=True)
    business_metrics = BusinessMetricsSerializer()
    service_health = ServiceHealthSerializer()
    provider_balances = ProviderBalancesSerializer()
    alerts = AlertsSerializer()
    quick_actions = QuickActionsSerializer()
    finances = FinanceStatsSerializer()
