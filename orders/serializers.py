from rest_framework import serializers
from .models import (
    DataService, DataVariation, AirtimeNetwork, 
    ElectricityService, ElectricityVariation, 
    Purchase, TVService, TVVariation,
    InternetVariation, PromoCode, EducationService, EducationVariation,
    PurchaseBeneficiary
)


# ─── Model Serializers ───

class DataServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataService
        fields = "__all__"

class PurchaseBeneficiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseBeneficiary
        fields = ['id', 'service_type', 'identifier', 'nickname', 'created_at']
        read_only_fields = ['id', 'created_at']

class DataVariationSerializer(serializers.ModelSerializer):
    service = DataServiceSerializer(read_only=True)
    selling_price = serializers.SerializerMethodField()
    agent_price = serializers.SerializerMethodField()

    class Meta:
        model = DataVariation
        fields = ["id", "name", "service", "variation_id", "selling_price", "agent_price", "plan_type", "is_active"]

    def get_selling_price(self, obj):
        from .models import ServiceRouting
        routing = ServiceRouting.objects.filter(service='data').first()
        if routing and routing.pricing_mode == 'fixed_margin' and routing.customer_margin > 0:
            return float(obj.cost_price + routing.customer_margin)
        return float(obj.selling_price)

    def get_agent_price(self, obj):
        from .models import ServiceRouting
        routing = ServiceRouting.objects.filter(service='data').first()
        if routing and routing.pricing_mode == 'fixed_margin' and routing.agent_margin > 0:
            return float(obj.cost_price + routing.agent_margin)
        return float(obj.agent_price)

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
        fields = ["id", "name", "service", "variation_id", "discount", "agent_discount", "plan_type", "is_active"]

class TVServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TVService
        fields="__all__"

class TVVariationSerializer(serializers.ModelSerializer):
    service = TVServiceSerializer(read_only=True)
    selling_price = serializers.SerializerMethodField()
    agent_price = serializers.SerializerMethodField()

    class Meta:
        model = TVVariation
        fields = ["id", "name", "service", "variation_id", "selling_price", "agent_price", "plan_type", "is_active"]

    def get_selling_price(self, obj):
        from .models import ServiceRouting
        routing = ServiceRouting.objects.filter(service='tv').first()
        if routing and routing.pricing_mode == 'fixed_margin' and routing.customer_margin > 0:
            return float(obj.cost_price + routing.customer_margin)
        return float(obj.selling_price)

    def get_agent_price(self, obj):
        from .models import ServiceRouting
        routing = ServiceRouting.objects.filter(service='tv').first()
        if routing and routing.pricing_mode == 'fixed_margin' and routing.agent_margin > 0:
            return float(obj.cost_price + routing.agent_margin)
        return float(obj.agent_price)

class InternetVariationSerializer(serializers.ModelSerializer):
    selling_price = serializers.SerializerMethodField()
    agent_price = serializers.SerializerMethodField()

    class Meta:
        model = InternetVariation
        fields = ["id", "name", "variation_id", "selling_price", "agent_price", "plan_type", "is_active"]

    def get_selling_price(self, obj):
        from .models import ServiceRouting
        routing = ServiceRouting.objects.filter(service='internet').first()
        if routing and routing.pricing_mode == 'fixed_margin' and routing.customer_margin > 0:
            return float(obj.cost_price + routing.customer_margin)
        return float(obj.selling_price)

    def get_agent_price(self, obj):
        from .models import ServiceRouting
        routing = ServiceRouting.objects.filter(service='internet').first()
        if routing and routing.pricing_mode == 'fixed_margin' and routing.agent_margin > 0:
            return float(obj.cost_price + routing.agent_margin)
        return float(obj.agent_price)

class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = [
            "id", "purchase_type", "reference", "amount", "beneficiary", 
            "status", "initiator", "time", "remarks",
            "airtime_service", "data_variation", "electricity_service", 
            "electricity_variation", "tv_variation", "internet_variation", 
            "education_variation"
        ]

class PromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = ['code', 'discount_amount', 'discount_percentage', 'expiry_date', 'is_active']

class EducationServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationService
        fields = "__all__"

class EducationVariationSerializer(serializers.ModelSerializer):
    service = EducationServiceSerializer(read_only=True)
    selling_price = serializers.SerializerMethodField()
    agent_price = serializers.SerializerMethodField()

    class Meta:
        model = EducationVariation
        fields = ["id", "name", "service", "variation_id", "selling_price", "agent_price", "plan_type", "is_active"]

    def get_selling_price(self, obj):
        from .models import ServiceRouting
        routing = ServiceRouting.objects.filter(service='education').first()
        if routing and routing.pricing_mode == 'fixed_margin' and routing.customer_margin > 0:
            return float(obj.cost_price + routing.customer_margin)
        return float(obj.selling_price)

    def get_agent_price(self, obj):
        from .models import ServiceRouting
        routing = ServiceRouting.objects.filter(service='education').first()
        if routing and routing.pricing_mode == 'fixed_margin' and routing.agent_margin > 0:
            return float(obj.cost_price + routing.agent_margin)
        return float(obj.agent_price)


# ─── Purchase Request Serializers ───

class BasePurchaseRequestSerializer(serializers.Serializer):
    transaction_pin = serializers.CharField(max_length=4, write_only=True, help_text="4-digit transaction PIN")
    promo_code = serializers.CharField(max_length=50, required=False, allow_null=True, help_text="Optional promo code for discount")

class DataPurchaseRequestSerializer(BasePurchaseRequestSerializer):
    plan_id = serializers.IntegerField(help_text="ID of the data variation/plan to purchase")
    phone_number = serializers.CharField(max_length=20, help_text="Beneficiary phone number e.g. 08012345678")

class AirtimePurchaseRequestSerializer(BasePurchaseRequestSerializer):
    service_id = serializers.CharField(help_text="Network service ID e.g. 'mtn', 'glo'")
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Airtime amount in Naira")
    phone_number = serializers.CharField(max_length=20, help_text="Beneficiary phone number e.g. 08012345678")

class ElectricityPurchaseRequestSerializer(BasePurchaseRequestSerializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Amount to pay in Naira")
    service_id = serializers.CharField(help_text="Disco service ID e.g. 'ikedc-postpaid'")
    variation_id = serializers.CharField(max_length=50, help_text="Electricity variation ID e.g. 'prepaid'")
    customer_id = serializers.CharField(max_length=20, help_text="Meter number")

class TVPurchaseRequestSerializer(BasePurchaseRequestSerializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Subscription amount in Naira")
    service_id = serializers.CharField(help_text="TV service ID e.g. 'dstv', 'gotv'")
    customer_id = serializers.CharField(max_length=50, help_text="Smartcard / IUC number")
    subscription_type = serializers.CharField(max_length=50, help_text="Subscription type e.g. 'renew'")
    variation_id = serializers.CharField(max_length=50, help_text="TV package variation ID")

class InternetPurchaseRequestSerializer(BasePurchaseRequestSerializer):
    plan_id = serializers.IntegerField(help_text="ID of the Internet variation/plan")
    phone_number = serializers.CharField(help_text="Beneficiary Internet sub account phone number")

class EducationPurchaseRequestSerializer(BasePurchaseRequestSerializer):
    service_id = serializers.CharField(help_text="Education service ID e.g. 'waec', 'neco'")
    variation_id = serializers.CharField(help_text="Education variation ID")
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="PIN price in Naira")


# ─── Utility Request/Response Serializers ───

class VerifyCustomerRequestSerializer(serializers.Serializer):
    service_id = serializers.CharField(help_text="Service ID for the provider e.g. 'dstv', 'ikedc-postpaid'")
    customer_id = serializers.CharField(help_text="Customer identifier e.g. smartcard number or meter number")
    purchase_type = serializers.ChoiceField(
        choices=['tv', 'electricity', 'internet'], 
        default='tv',
        help_text="Type of verification: 'tv', 'electricity', or 'internet'"
    )

class VerifyCustomerResponseSerializer(serializers.Serializer):
    account_name = serializers.CharField(help_text="Name of the verified customer")
    raw_response = serializers.DictField(required=False, help_text="Raw provider response")

class RepeatPurchaseRequestSerializer(serializers.Serializer):
    purchase_id = serializers.IntegerField(help_text="ID of the previous purchase to repeat")


# ─── Generic Response Serializers ───

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField(help_text="Error message describing the failure")

class SuccessMessageSerializer(serializers.Serializer):
    status = serializers.CharField(help_text="Status of the operation e.g. 'SUCCESS'")
    message = serializers.CharField(help_text="Human-readable success message")
