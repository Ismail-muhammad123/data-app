from rest_framework import serializers

class InitFundWalletRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, help_text="Minimum 100. Amount to deposit in Naira.")

class InitFundWalletResponseSerializer(serializers.Serializer):
    message = serializers.CharField(help_text="Funding initiated message")
    response = serializers.DictField(help_text="Paystack payment initialization response with authorization_url")

class ChargesConfigResponseSerializer(serializers.Serializer):
    withdrawal_charge = serializers.FloatField(help_text="Withdrawal fee in Naira")
    deposit_charge = serializers.FloatField(help_text="Deposit/credit charge in Naira")

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField(help_text="Error message describing the failure")

class SuccessMessageSerializer(serializers.Serializer):
    message = serializers.CharField(help_text="Success message")
