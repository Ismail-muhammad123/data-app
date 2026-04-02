from rest_framework import serializers
from users.models import User, StaffPermission, ReferralConfig, KYC
from admin_api.models import AdminBeneficiary, AdminTransferLog
from orders.models import (
    VTUProviderConfig, ServiceRouting, ServiceFallback, Purchase, 
    DataVariation, AirtimeNetwork, TVVariation, SmileVariation, 
    EducationVariation, ElectricityVariation, PromoCode
)
from payments.models import PaymentGatewayConfig, Deposit, Withdrawal
from wallet.models import Wallet, WalletTransaction
from support.models import SupportTicket, TicketMessage
from notifications.models import NotificationLog, Announcement, NotificationProviderConfig


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

class AdminUserSerializer(serializers.ModelSerializer):
    staff_permissions = StaffPermissionSerializer(required=False)
    wallet_balance = serializers.DecimalField(source='wallet.balance', max_digits=12, decimal_places=2, read_only=True)
    kyc = KYCSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            "id", "phone_number", "first_name", "last_name", "email", "role", 
            "is_active", "is_verified", "is_kyc_verified", "is_staff", 
            "is_superuser", "referral_code", "wallet_balance",
            "referral_earnings_count", "referral_earnings_amount",
            "staff_permissions", "kyc"
        ]

class VTUProviderConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = VTUProviderConfig
        fields = '__all__'

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

class AdminNotificationLogSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    class Meta:
        model = NotificationLog
        fields = '__all__'

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

class AdminSmileVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmileVariation
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
    purchase_type = serializers.ChoiceField(choices=['data', 'airtime', 'electricity', 'tv', 'smile', 'education'], help_text="Type of purchase")
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

class AdminStatusResponseSerializer(serializers.Serializer):
    status = serializers.CharField(help_text="Status of the operation e.g. 'SUCCESS', 'REJECTED'")
    message = serializers.CharField(help_text="Human-readable result message")

class AdminDashboardStatsResponseSerializer(serializers.Serializer):
    class UserStatsSerializer(serializers.Serializer):
        total = serializers.IntegerField(help_text="Total registered users")

    class FinanceStatsSerializer(serializers.Serializer):
        total_deposits = serializers.DecimalField(max_digits=15, decimal_places=2, help_text="Sum of all successful deposits")

    class TransactionStatsSerializer(serializers.Serializer):
        total = serializers.IntegerField(help_text="Total number of purchases")

    users = UserStatsSerializer()
    finances = FinanceStatsSerializer()
    transactions = TransactionStatsSerializer()

class AdminErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField(help_text="Error message")
