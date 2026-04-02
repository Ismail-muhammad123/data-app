from rest_framework import serializers
from users.models import User, StaffPermission, ReferralConfig, KYC
from admin_api.models import AdminBeneficiary, AdminTransferLog
from orders.models import (
    VTUProviderConfig, ServiceRouting, ServiceFallback, Purchase, 
    DataVariation, AirtimeNetwork, TVVariation, InternetVariation, 
    EducationVariation, ElectricityVariation, PromoCode
)
from payments.models import PaymentGatewayConfig, Deposit, Withdrawal
from wallet.models import Wallet, WalletTransaction
from support.models import SupportTicket, TicketMessage
from notifications.models import Notification, UserNotification, Announcement, NotificationProviderConfig


# ─── Model Serializers ───

class AdminBeneficiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminBeneficiary
        fields = '__all__'

class StaffPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffPermission
        fields = '__all__'

class KYCSerializer(serializers.ModelSerializer):
    processed_by_name = serializers.CharField(source='processed_by.phone_number', read_only=True)
    class Meta:
        model = KYC
        fields = '__all__'

class AdminUserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the user list endpoint."""
    wallet_balance = serializers.DecimalField(source='wallet.balance', max_digits=12, decimal_places=2, read_only=True, default=0)

    class Meta:
        model = User
        fields = [
            "id", "phone_number", "first_name", "last_name", "email", "role",
            "is_active", "is_verified", "is_kyc_verified", "is_staff",
            "is_closed", "referral_code", "wallet_balance", "created_at",
        ]


class AdminUserDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer for a single user view."""
    staff_permissions = StaffPermissionSerializer(required=False, read_only=True)
    wallet_balance = serializers.DecimalField(source='wallet.balance', max_digits=12, decimal_places=2, read_only=True, default=0)
    kyc = KYCSerializer(read_only=True)
    virtual_account = serializers.SerializerMethodField()
    beneficiaries = serializers.SerializerMethodField()
    purchase_beneficiaries = serializers.SerializerMethodField()
    transfer_beneficiaries = serializers.SerializerMethodField()
    recent_transactions = serializers.SerializerMethodField()
    recent_purchases = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "phone_number", "first_name", "last_name", "middle_name", "email",
            "phone_country_code", "role", "agent_commission_rate",
            "is_active", "is_verified", "is_kyc_verified", "is_staff", "is_superuser",
            "is_closed", "closed_at", "closed_reason",
            "referral_code", "referral_earnings_count", "referral_earnings_amount",
            "transaction_pin_set", "two_factor_enabled", "profile_picture_url",
            "wallet_balance", "kyc", "staff_permissions", "virtual_account",
            "beneficiaries", "purchase_beneficiaries", "transfer_beneficiaries",
            "recent_transactions", "recent_purchases",
            "created_at", "upgraded_at",
        ]

    def get_virtual_account(self, obj):
        from wallet.models import VirtualAccount
        try:
            va = obj.virtual_account
            return {
                "account_number": va.account_number,
                "bank_name": va.bank_name,
                "account_name": va.account_name,
            }
        except VirtualAccount.DoesNotExist:
            return None

    def get_beneficiaries(self, obj):
        from users.models import Beneficiary
        return list(obj.beneficiaries.values("id", "service_type", "identifier", "nickname")[:20])

    def get_purchase_beneficiaries(self, obj):
        from orders.models import PurchaseBeneficiary
        return list(obj.purchase_beneficiaries.values("id", "service_type", "identifier", "nickname")[:20])

    def get_transfer_beneficiaries(self, obj):
        from wallet.models import TransferBeneficiary
        return list(obj.transfer_beneficiaries.values("id", "bank_name", "account_number", "account_name", "nickname")[:20])

    def get_recent_transactions(self, obj):
        txs = obj.wallet_transactions.order_by('-timestamp')[:15]
        return [{
            "id": t.id, "type": t.transaction_type, "amount": float(t.amount),
            "balance_after": float(t.balance_after), "description": t.description,
            "reference": t.reference, "timestamp": t.timestamp.isoformat(),
        } for t in txs]

    def get_recent_purchases(self, obj):
        purchases = obj.purchases.order_by('-time')[:15]
        return [{
            "id": p.id, "type": p.purchase_type, "amount": float(p.amount),
            "beneficiary": p.beneficiary, "status": p.status,
            "reference": p.reference, "time": p.time.isoformat(),
        } for p in purchases]


class AdminCreateUserRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(help_text="User phone number (unique)")
    first_name = serializers.CharField(required=False, help_text="First name")
    last_name = serializers.CharField(required=False, help_text="Last name")
    email = serializers.EmailField(required=False, help_text="Email address")
    password = serializers.CharField(help_text="Login password/PIN")
    role = serializers.ChoiceField(choices=['customer', 'agent', 'staff'], default='customer', help_text="User role")
    is_active = serializers.BooleanField(default=True)


class AdminSetRoleRequestSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['customer', 'agent', 'staff'], help_text="New role for the user")
    commission_rate = serializers.FloatField(required=False, default=0.0, help_text="Agent commission rate (only for agent role)")


class AdminSetPermissionsRequestSerializer(serializers.Serializer):
    can_manage_users = serializers.BooleanField(required=False, default=False)
    can_manage_wallets = serializers.BooleanField(required=False, default=False)
    can_manage_vtu = serializers.BooleanField(required=False, default=False)
    can_manage_payments = serializers.BooleanField(required=False, default=False)
    can_manage_notifications = serializers.BooleanField(required=False, default=False)
    can_manage_site_config = serializers.BooleanField(required=False, default=False)
    can_initiate_transfers = serializers.BooleanField(required=False, default=False)


class AdminResetPinRequestSerializer(serializers.Serializer):
    new_pin = serializers.CharField(min_length=4, max_length=6, help_text="New transaction PIN for the user")


class VTUProviderConfigSerializer(serializers.ModelSerializer):
    webhook_url = serializers.ReadOnlyField()
    callback_url = serializers.ReadOnlyField()
    
    class Meta:
        model = VTUProviderConfig
        fields = [
            'id', 'name', 'is_active', 'api_key', 'user_id', 'session_id', 
            'private_key', 'public_key', 'base_url', 'config_data', 
            'webhook_url', 'callback_url', 'max_retries', 'auto_refund_on_failure',
            'account_name', 'bank_name', 'account_number', 'bank_code', 
            'min_funding_balance', 'auto_funding_enabled'
        ]

class ServiceFallbackSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.get_name_display', read_only=True)
    class Meta:
        model = ServiceFallback
        fields = ["id", "provider", "provider_name", "priority"]

class ServiceRoutingSerializer(serializers.ModelSerializer):
    fallbacks = ServiceFallbackSerializer(source='servicefallback_set', many=True, read_only=True)
    primary_provider_name = serializers.CharField(source='primary_provider.get_name_display', read_only=True)
    class Meta:
        model = ServiceRouting
        fields = ["id", "service", "primary_provider", "primary_provider_name", "fallbacks"]

class PaymentGatewayConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentGatewayConfig
        fields = '__all__'

class AdminTransferLogSerializer(serializers.ModelSerializer):
    beneficiary_name = serializers.CharField(source='beneficiary.name', read_only=True)
    class Meta:
        model = AdminTransferLog
        fields = '__all__'

class AdminPurchaseSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    class Meta:
        model = Purchase
        fields = '__all__'

class AdminDepositSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.phone_number', read_only=True)
    class Meta:
        model = Deposit
        fields = '__all__'

class AdminWithdrawalSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.phone_number', read_only=True)
    class Meta:
        model = Withdrawal
        fields = '__all__'

class AdminWalletTransactionSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    class Meta:
        model = WalletTransaction
        fields = '__all__'


class AdminTicketMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.phone_number', read_only=True)
    class Meta:
        model = TicketMessage
        fields = '__all__'

class AdminSupportTicketSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    messages = AdminTicketMessageSerializer(many=True, read_only=True)
    class Meta:
        model = SupportTicket
        fields = '__all__'

class AdminUserNotificationSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    class Meta:
        model = UserNotification
        fields = ["id", "user", "user_phone", "is_read", "read_at", "status", "error_message", "created_at"]

class AdminNotificationSerializer(serializers.ModelSerializer):
    recipients_count = serializers.SerializerMethodField()
    recipients = AdminUserNotificationSerializer(source='user_notifications', many=True, read_only=True)
    
    class Meta:
        model = Notification
        fields = ["id", "title", "body", "channel", "data", "recipients_count", "recipients", "created_at"]

    def get_recipients_count(self, obj):
        return obj.user_notifications.count()

class AdminAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = '__all__'

class AdminNotificationProviderConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationProviderConfig
        fields = '__all__'

class AdminReferralConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralConfig
        fields = '__all__'

# ─── Variations Serializers for Admin (includes agent pricing) ───

class AdminDataVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataVariation
        fields = '__all__'

class AdminAirtimeNetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirtimeNetwork
        fields = '__all__'

class AdminTVVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TVVariation
        fields = '__all__'

class AdminInternetVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternetVariation
        fields = '__all__'

class AdminEducationVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationVariation
        fields = '__all__'

class AdminElectricityVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectricityVariation
        fields = '__all__'

class AdminPromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = '__all__'


# ─── Admin Action Request Serializers ───

class AdminKYCActionRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, help_text="Reason for approval/rejection")

class AdminAgentUpgradeRequestSerializer(serializers.Serializer):
    commission_rate = serializers.FloatField(required=False, default=0.0, help_text="Agent commission rate percentage")

class AdminManualAdjustmentRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(help_text="Target user ID")
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, help_text="Amount to credit or debit")
    type = serializers.ChoiceField(choices=['credit', 'debit'], help_text="Type of adjustment: 'credit' or 'debit'")
    reason = serializers.CharField(required=False, default="Admin Adjustment", help_text="Reason for the adjustment")

class AdminDepositMarkSuccessRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, default="Manually confirmed by Admin", help_text="Admin remark for manual confirmation")

class AdminWithdrawalActionRequestSerializer(serializers.Serializer):
    otp = serializers.CharField(required=False, help_text="Admin 2FA OTP code (required if 2FA is enabled)")
    reason = serializers.CharField(required=False, help_text="Reason for approval/rejection")

class AdminCreatePurchaseRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(help_text="User ID to initiate purchase for")
    purchase_type = serializers.ChoiceField(choices=['data', 'airtime', 'electricity', 'tv', 'internet', 'education'], help_text="Type of purchase")
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Purchase amount")
    beneficiary = serializers.CharField(help_text="Beneficiary phone/meter/smartcard number")
    action = serializers.CharField(help_text="Action name e.g. 'buy_data', 'buy_airtime'")
    extra_kwargs = serializers.DictField(required=False, default={}, help_text="Additional kwargs for the purchase")

class AdminSupportReplyRequestSerializer(serializers.Serializer):
    message = serializers.CharField(help_text="Reply message content")

class AdminInitiateTransferRequestSerializer(serializers.Serializer):
    beneficiary_id = serializers.IntegerField(help_text="Admin beneficiary ID")
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, help_text="Transfer amount in Naira")
    otp = serializers.CharField(required=False, help_text="Admin 2FA OTP code (required if 2FA is enabled)")


# ─── Admin Action Response Serializers ───

class AdminErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField(help_text="Error message")

class AdminPauseServiceRequestSerializer(serializers.Serializer):
    service = serializers.ChoiceField(
        choices=['airtime', 'data', 'tv', 'electricity', 'education'],
        help_text="Service to pause or resume"
    )
    active = serializers.BooleanField(help_text="Set to true to resume, false to pause")


class AdminStatusResponseSerializer(serializers.Serializer):
    status = serializers.CharField(help_text="Status of the operation e.g. 'SUCCESS', 'REJECTED'")
    message = serializers.CharField(help_text="Human-readable result message")

class AdminDashboardStatsResponseSerializer(serializers.Serializer):
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
            
        deposits = DepositStatsSerializer()
        withdrawals = WithdrawalStatsSerializer()

    business_metrics = BusinessMetricsSerializer()
    service_health = ServiceHealthSerializer()
    provider_balances = ProviderBalancesSerializer()
    alerts = AlertsSerializer()
    quick_actions = QuickActionsSerializer()
    finances = FinanceStatsSerializer()

# ─── Automation & VTU Management Serializers ───

class AutomationGlobalSettingsSerializer(serializers.Serializer):
    auto_retry_enabled = serializers.BooleanField()
    auto_refund_enabled = serializers.BooleanField()
    notify_admin_on_failure = serializers.BooleanField()
    delayed_tx_detection_enabled = serializers.BooleanField()
    delayed_tx_timeout_minutes = serializers.IntegerField(min_value=1)

class ServiceAutomationConfigSerializer(serializers.ModelSerializer):
    primary_provider_name = serializers.CharField(source='primary_provider.get_name_display', read_only=True)
    class Meta:
        model = ServiceRouting
        fields = [
            'id', 'service', 'primary_provider', 'primary_provider_name',
            'retry_enabled', 'retry_count', 'auto_refund_enabled', 'fallback_enabled',
            'pricing_mode', 'customer_margin', 'agent_margin'
        ]

class AutomationOverviewResponseSerializer(serializers.Serializer):
    global_settings = AutomationGlobalSettingsSerializer()
    services = ServiceAutomationConfigSerializer(many=True)

class AdminNotificationOverviewSerializer(serializers.Serializer):
    notifications = AdminNotificationSerializer(many=True)
    announcements = AdminAnnouncementSerializer(many=True)

class AdminBulkSendNotificationSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.IntegerField(), help_text="IDs of target users")
    title = serializers.CharField()
    body = serializers.CharField()
    channel = serializers.ChoiceField(choices=['fcm', 'email', 'sms', 'whatsapp'])
    data = serializers.JSONField(required=False, default={})

class VTUProviderOverviewSerializer(serializers.ModelSerializer):
    balance = serializers.FloatField(required=False)
    class Meta:
        model = VTUProviderConfig
        fields = [
            'id', 'name', 'is_active', 'balance', 'account_name', 
            'bank_name', 'account_number', 'bank_code', 
            'min_funding_balance', 'auto_funding_enabled'
        ]

class AvailableVTUProviderSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()

class VTUOverviewResponseSerializer(serializers.Serializer):
    providers = VTUProviderOverviewSerializer(many=True)
    services_summary = serializers.ListField(child=serializers.DictField())

class FetchFromProviderRequestSerializer(serializers.Serializer):
    provider_id = serializers.IntegerField()
    service_type = serializers.ChoiceField(choices=['airtime', 'data', 'tv', 'electricity', 'internet', 'education'])

class VariationPriceUpdateSerializer(serializers.Serializer):
    selling_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    agent_price = serializers.DecimalField(max_digits=10, decimal_places=2)

class BulkVariationPriceItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    selling_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    agent_price = serializers.DecimalField(max_digits=10, decimal_places=2)

class BulkVariationPriceUpdateSerializer(serializers.Serializer):
    variations = BulkVariationPriceItemSerializer(many=True)

class VariationToggleSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()

class ServiceTypeToggleSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()

class ServiceRetryConfigSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    count = serializers.IntegerField(min_value=0, max_value=10)

class ServicePricingModeSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=['fixed_margin', 'defined'])
    customer_margin = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    agent_margin = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

class ProviderFundingConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = VTUProviderConfig
        fields = ['account_name', 'bank_name', 'account_number', 'bank_code', 'min_funding_balance', 'auto_funding_enabled']
