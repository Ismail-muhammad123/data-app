from rest_framework import serializers
from .models import Wallet, WalletTransaction, VirtualAccount, WithdrawalAccount



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

class WithdrawalAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalAccount
        fields = ["bank_name", "bank_code", "account_number", "account_name", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

class ResolveAccountSerializer(serializers.Serializer):
    account_number = serializers.CharField(max_length=20)
    bank_code = serializers.CharField(max_length=10)
