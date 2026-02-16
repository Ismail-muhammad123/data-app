from rest_framework import serializers
from .models import (
    DataService, DataVariation, AirtimeNetwork, 
    ElectricityService, ElectricityVariation, 
    Purchase, TVService, TVVariation,
    SmileVariation
)


class DataServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataService
        fields = "__all__"

class DataVariationSerializer(serializers.ModelSerializer):
    service = DataServiceSerializer(read_only=True)
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

class ElectricityServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectricityService
        fields="__all__"

class ElectricityVariationSerializer(serializers.ModelSerializer):
    service = ElectricityServiceSerializer(read_only=True)
    class Meta:
        model = ElectricityVariation
        fields = ["id", "name", "service", "variation_id", "is_active"]

class TVServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TVService
        fields="__all__"

class TVVariationSerializer(serializers.ModelSerializer):
    service = TVServiceSerializer(read_only=True)
    class Meta:
        model = TVVariation
        fields = [
            "id",
            "name",
            "service",
            "variation_id",
            "selling_price",
            "is_active",
        ]

class SmileVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmileVariation
        fields = [
            "id",
            "name",
            "variation_id",
            "selling_price",
            "is_active",
        ]

class ElectricityPurchaseRequestSerializer(serializers.Serializer):
    amount = serializers.IntegerField()
    service_id = serializers.CharField()
    variation_id = serializers.CharField(max_length=50)
    customer_id = serializers.CharField(max_length=20)


class TVPurchaseRequestSerializer(serializers.Serializer):
    amount = serializers.IntegerField()
    service_id = serializers.CharField()
    customer_id = serializers.CharField(max_length=50)
    subscription_type =serializers.CharField(max_length=50)
    variation_id = serializers.CharField(max_length=50)

class SmilePurchaseRequestSerializer(serializers.Serializer):
    amount = serializers.IntegerField()
    service_id = serializers.CharField()
    customer_id = serializers.CharField(max_length=50)
    variation_id = serializers.CharField(max_length=50)

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

