from rest_framework import serializers
from .models import (
    Wallet, WalletTransaction, VirtualAccount, TransferBeneficiary
)


# ─── Model Serializers ───

class VirtualAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualAccount
        fields = "__all__"
        read_only_fields = ["user", "created_at"]

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'balance']

class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 
            'amount', 
            'transaction_type', 
            'description', 
            'timestamp',
            'initiator',
        ]

class TransferBeneficiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferBeneficiary
        fields = ['id', 'bank_name', 'bank_code', 'account_number', 'account_name', 'nickname', 'created_at']
        read_only_fields = ['id', 'created_at']


# ─── Request Serializers ───

class ResolveAccountSerializer(serializers.Serializer):
    account_number = serializers.CharField(max_length=20, help_text="Bank account number e.g. '0123456789'")
    bank_code = serializers.CharField(max_length=10, help_text="Bank sort code e.g. '058'")

class WalletTransferSerializer(serializers.Serializer):
    recipient_phone = serializers.CharField(help_text="Recipient phone number e.g. '08012345678'")
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, help_text="Transfer amount in Naira")
    description = serializers.CharField(required=False, allow_blank=True, help_text="Optional transfer narration")
    transaction_pin = serializers.CharField(min_length=4, max_length=4, help_text="4-digit transaction PIN")

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

class BankTransferRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, help_text="Withdrawal amount in Naira")
    bank_name = serializers.CharField(max_length=100, help_text="Name of the destination bank e.g. 'GTBank'")
    bank_code = serializers.CharField(max_length=10, help_text="Bank sort code e.g. '058'")
    account_number = serializers.CharField(max_length=20, help_text="Destination account number")
    account_name = serializers.CharField(max_length=200, help_text="Account holder name")
    transaction_pin = serializers.CharField(min_length=4, max_length=4, write_only=True, help_text="4-digit transaction PIN")

class InitFundWalletRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, help_text="Minimum 100. Amount to deposit in Naira.")

class VerifyRecipientRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(help_text="Phone number of the recipient to look up e.g. '08012345678'")


# ─── Response Serializers ───

class WalletTransferResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(help_text="Whether the transfer was successful")
    message = serializers.CharField(help_text="Human-readable result message")

class BankTransferResponseSerializer(serializers.Serializer):
    message = serializers.CharField(help_text="Success message")
    reference = serializers.CharField(help_text="Withdrawal reference e.g. 'WTH-ABC12345DEF'")

class InitFundWalletResponseSerializer(serializers.Serializer):
    message = serializers.CharField(help_text="Funding initiated message")
    response = serializers.DictField(help_text="Paystack payment initialization response with authorization_url")

class VerifyRecipientResponseSerializer(serializers.Serializer):
    full_name = serializers.CharField(help_text="Recipient full name")
    phone_number = serializers.CharField(help_text="Recipient phone number")
    profile_image = serializers.URLField(allow_null=True, help_text="Profile image URL or null")

class ResolveAccountResponseSerializer(serializers.Serializer):
    account_number = serializers.CharField(help_text="Resolved account number")
    account_name = serializers.CharField(help_text="Account holder name")
    bank_id = serializers.IntegerField(required=False, help_text="Bank ID")

class BankListItemSerializer(serializers.Serializer):
    name = serializers.CharField(help_text="Bank name")
    code = serializers.CharField(help_text="Bank sort code")

class ChargesConfigResponseSerializer(serializers.Serializer):
    withdrawal_charge = serializers.FloatField(help_text="Withdrawal fee in Naira")
    deposit_charge = serializers.FloatField(help_text="Deposit/credit charge in Naira")

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField(help_text="Error message describing the failure")

class SuccessMessageSerializer(serializers.Serializer):
    message = serializers.CharField(help_text="Success message")
