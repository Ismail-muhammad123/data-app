from rest_framework import serializers
from admin_api.models import AdminBeneficiary, AdminTransferLog
from payments.models import PaystackConfig, Deposit, Withdrawal, AdminTransfer, AdminTransferBeneficiary
from orders.models import Purchase
from wallet.models import WalletTransaction

class AdminBeneficiarySerializer(serializers.ModelSerializer):
    class Meta: model = AdminBeneficiary; fields = '__all__'

class AdminTransferLogSerializer(serializers.ModelSerializer):
    beneficiary_name = serializers.CharField(source='beneficiary.name', read_only=True)
    class Meta: model = AdminTransferLog; fields = '__all__'

class AdminPaystackConfigSerializer(serializers.ModelSerializer):
    webhook_url, callback_url = serializers.ReadOnlyField(), serializers.ReadOnlyField()
    class Meta: model = PaystackConfig; fields = ["id", "is_active", "public_key", "secret_key", "webhook_url", "callback_url"]

class AdminPurchaseSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    class Meta: model = Purchase; fields = '__all__'

class AdminDepositSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone_number', read_only=True); processed_by_name = serializers.CharField(source='processed_by.phone_number', read_only=True)
    class Meta: model = Deposit; fields = '__all__'

class AdminWithdrawalSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone_number', read_only=True); processed_by_name = serializers.CharField(source='processed_by.phone_number', read_only=True)
    class Meta: model = Withdrawal; fields = '__all__'

class AdminWalletTransactionSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    class Meta: model = WalletTransaction; fields = '__all__'

class AdminTransferBeneficiarySerializer(serializers.ModelSerializer):
    class Meta: model = AdminTransferBeneficiary; fields = '__all__'

class AdminTransferSerializer(serializers.ModelSerializer):
    beneficiary_details = AdminTransferBeneficiarySerializer(source='beneficiary', read_only=True); initiated_by_name = serializers.CharField(source='initiated_by.phone_number', read_only=True)
    class Meta: model = AdminTransfer; fields = '__all__'

class AdminManualAdjustmentRequestSerializer(serializers.Serializer):
    user_id, amount, reason, pin = serializers.IntegerField(), serializers.DecimalField(max_digits=12, decimal_places=2), serializers.CharField(required=False, default="Admin Adjustment"), serializers.CharField()
    type = serializers.ChoiceField(choices=['credit', 'debit'])

class AdminInitiateTransferRequestSerializer(serializers.Serializer):
    beneficiary_id, amount, pin = serializers.IntegerField(), serializers.DecimalField(max_digits=12, decimal_places=2), serializers.CharField()
