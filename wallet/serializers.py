from rest_framework import serializers
from .models import Wallet, WalletTransaction, VirtualAccount



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
