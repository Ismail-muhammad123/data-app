from rest_framework import serializers
from .models import DataNetwork, DataPlan, AirtimeNetwork, Purchase 


class DataNetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataNetwork
        fields = "__all__"

class DataPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataPlan
        fields = "__all__"

class AirtimeNetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirtimeNetwork
        fields="__all__"


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields= "__all__"

class DataPurchaseRequestSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    phone_number = serializers.CharField(max_length=20)


class AirtimePurchaseRequestSerializer(serializers.Serializer):
    network_id = serializers.IntegerField()
    amount = serializers.IntegerField()
    phone_number = serializers.CharField(max_length=20)
