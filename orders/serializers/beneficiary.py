from rest_framework import serializers
from orders.models import PurchaseBeneficiary

class PurchaseBeneficiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseBeneficiary
        fields = ['id', 'service_type', 'identifier', 'nickname', 'created_at']
        read_only_fields = ['id', 'created_at']
