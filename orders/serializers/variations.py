from rest_framework import serializers
from orders.models import (
    DataService, DataVariation, AirtimeNetwork, ElectricityService, ElectricityVariation, 
    TVService, TVVariation, InternetService, InternetVariation, EducationService, EducationVariation, PromoCode
)

class DataServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataService; fields = "__all__"

class DataVariationSerializer(serializers.ModelSerializer):
    service = DataServiceSerializer(read_only=True)
    selling_price, agent_price = serializers.SerializerMethodField(), serializers.SerializerMethodField()
    class Meta:
        model = DataVariation; fields = ["id", "name", "service", "variation_id", "selling_price", "agent_price", "plan_type", "is_active"]
    def get_selling_price(self, obj):
        from .models import ServiceRouting
        r = ServiceRouting.objects.filter(service='data').first()
        return float(obj.cost_price + r.customer_margin) if r and r.pricing_mode == 'fixed_margin' else float(obj.selling_price)
    def get_agent_price(self, obj):
        from .models import ServiceRouting
        r = ServiceRouting.objects.filter(service='data').first()
        return float(obj.cost_price + r.agent_margin) if r and r.pricing_mode == 'fixed_margin' else float(obj.agent_price)

class AirtimeNetworkSerializer(serializers.ModelSerializer):
    class Meta: model = AirtimeNetwork; fields="__all__"

class ElectricityServiceSerializer(serializers.ModelSerializer):
    class Meta: model = ElectricityService; fields="__all__"

class ElectricityVariationSerializer(serializers.ModelSerializer):
    service = ElectricityServiceSerializer(read_only=True)
    class Meta: model = ElectricityVariation; fields = ["id", "name", "service", "variation_id", "discount", "agent_discount", "plan_type", "is_active"]

class TVServiceSerializer(serializers.ModelSerializer):
    class Meta: model = TVService; fields="__all__"

class TVVariationSerializer(serializers.ModelSerializer):
    service = TVServiceSerializer(read_only=True)
    selling_price, agent_price = serializers.SerializerMethodField(), serializers.SerializerMethodField()
    class Meta: model = TVVariation; fields = ["id", "name", "service", "variation_id", "selling_price", "agent_price", "plan_type", "is_active"]
    def get_selling_price(self, obj):
        from .models import ServiceRouting
        r = ServiceRouting.objects.filter(service='tv').first()
        return float(obj.cost_price + r.customer_margin) if r and r.pricing_mode == 'fixed_margin' else float(obj.selling_price)
    def get_agent_price(self, obj):
        from .models import ServiceRouting
        r = ServiceRouting.objects.filter(service='tv').first()
        return float(obj.cost_price + r.agent_margin) if r and r.pricing_mode == 'fixed_margin' else float(obj.agent_price)

class InternetServiceSerializer(serializers.ModelSerializer):
    class Meta: model = InternetService; fields = "__all__"

class InternetVariationSerializer(serializers.ModelSerializer):
    service = InternetServiceSerializer(read_only=True)
    selling_price, agent_price = serializers.SerializerMethodField(), serializers.SerializerMethodField()
    class Meta: model = InternetVariation; fields = ["id", "name", "service", "variation_id", "selling_price", "agent_price", "plan_type", "is_active"]
    def get_selling_price(self, obj):
        from .models import ServiceRouting
        r = ServiceRouting.objects.filter(service='internet').first()
        return float(obj.cost_price + r.customer_margin) if r and r.pricing_mode == 'fixed_margin' else float(obj.selling_price)
    def get_agent_price(self, obj):
        from .models import ServiceRouting
        r = ServiceRouting.objects.filter(service='internet').first()
        return float(obj.cost_price + r.agent_margin) if r and r.pricing_mode == 'fixed_margin' else float(obj.agent_price)

class PromoCodeSerializer(serializers.ModelSerializer):
    class Meta: model = PromoCode; fields = ['code', 'discount_amount', 'discount_percentage', 'expiry_date', 'is_active']

class EducationServiceSerializer(serializers.ModelSerializer):
    class Meta: model = EducationService; fields = "__all__"

class EducationVariationSerializer(serializers.ModelSerializer):
    service = EducationServiceSerializer(read_only=True)
    selling_price, agent_price = serializers.SerializerMethodField(), serializers.SerializerMethodField()
    class Meta: model = EducationVariation; fields = ["id", "name", "service", "variation_id", "selling_price", "agent_price", "plan_type", "is_active"]
    def get_selling_price(self, obj):
        from .models import ServiceRouting
        r = ServiceRouting.objects.filter(service='education').first()
        return float(obj.cost_price + r.customer_margin) if r and r.pricing_mode == 'fixed_margin' else float(obj.selling_price)
    def get_agent_price(self, obj):
        from .models import ServiceRouting
        r = ServiceRouting.objects.filter(service='education').first()
        return float(obj.cost_price + r.agent_margin) if r and r.pricing_mode == 'fixed_margin' else float(obj.agent_price)
