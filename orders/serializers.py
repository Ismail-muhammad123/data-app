from rest_framework import serializers
from .models import DataNetwork, DataPlan, DataSale, AirtimeNetwork, AirtimeSale


class DataNetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataNetwork
        fields = "__all__"

class DataPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataPlan
        fields = "__all__"


class DataSaleSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataSale
        fields = "__all__"


class AirtimeNetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirtimeNetwork
        field="__all__"


class AirtimeSaleSerializer(serializers.ModelSerializer):
    class Meta:
        models= AirtimeSale
        fields= "__all__"

class DataPurchaseRequestSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    phone_number = serializers.CharField(max_length=20)
