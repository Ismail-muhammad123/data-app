from rest_framework import serializers
from .models import DataService, DataVariation, AirtimeNetwork, Purchase 


class DataNetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataService
        fields = "__all__"

class DataPlanSerializer(serializers.ModelSerializer):
    service = DataNetworkSerializer(read_only=True)
    class Meta:
        model = DataVariation
        fields = [
            "id",
            "name",
            "service",
            "variation_id",
            "selling_price",
            "is_active",
        ]

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
    service_id = serializers.CharField()
    amount = serializers.IntegerField()
    phone_number = serializers.CharField(max_length=20)
