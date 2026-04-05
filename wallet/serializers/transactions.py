from rest_framework import serializers
from wallet.models import WalletTransaction

class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'amount', 'transaction_type', 'description', 'timestamp', 'initiator']
