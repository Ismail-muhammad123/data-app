from rest_framework import serializers
from wallet.models import TransferBeneficiary

class TransferBeneficiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferBeneficiary
        fields = ['id', 'bank_name', 'bank_code', 'account_number', 'account_name', 'nickname', 'created_at']
        read_only_fields = ['id', 'created_at']

class ResolveAccountSerializer(serializers.Serializer):
    account_number = serializers.CharField(max_length=20)
    bank_code = serializers.CharField(max_length=10)

class WalletTransferSerializer(serializers.Serializer):
    recipient_phone = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    description = serializers.CharField(required=False, allow_blank=True)
    transaction_pin = serializers.CharField(min_length=4, max_length=4)
    def validate_amount(self, value):
        if value <= 0: raise serializers.ValidationError("Amount must be greater than zero.")
        return value

class BankTransferRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    bank_name = serializers.CharField(max_length=100)
    bank_code = serializers.CharField(max_length=10)
    account_number = serializers.CharField(max_length=20)
    account_name = serializers.CharField(max_length=200)
    transaction_pin = serializers.CharField(min_length=4, max_length=4, write_only=True)

class VerifyRecipientRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

class WalletTransferResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()

class BankTransferResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    reference = serializers.CharField()

class VerifyRecipientResponseSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    phone_number = serializers.CharField()
    profile_image = serializers.URLField(allow_null=True)

class ResolveAccountResponseSerializer(serializers.Serializer):
    account_number = serializers.CharField()
    account_name = serializers.CharField()
    bank_id = serializers.IntegerField(required=False)

class BankListItemSerializer(serializers.Serializer):
    name = serializers.CharField()
    code = serializers.CharField()
