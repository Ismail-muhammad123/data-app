from rest_framework import serializers
from .models import Deposit, Withdrawal


class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = "__all__"
        read_only_fields = ("reference", "status", "timestamp")

class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = "__all__"
        read_only_fields = ["user", "status", "transaction_status", "reference", "transfer_code", "created_at", "updated_at"]