from rest_framework import serializers
from orders.models import (
    VTUProviderConfig, ServiceRouting, ServiceFallback, DataService, DataVariation, 
    AirtimeNetwork, TVService, TVVariation, InternetService, InternetVariation, 
    EducationService, EducationVariation, ElectricityService, ElectricityVariation
)

class VTUProviderConfigSerializer(serializers.ModelSerializer):
    webhook_url, callback_url = serializers.ReadOnlyField(), serializers.ReadOnlyField()
    class Meta:
        model = VTUProviderConfig
        fields = ['id', 'name', 'is_active', 'api_key', 'user_id', 'session_id', 'secret_key', 'public_key', 'base_url', 'webhook_url', 'callback_url', 'max_retries', 'auto_refund_on_failure', 'account_name', 'bank_name', 'account_number', 'bank_code', 'min_funding_balance', 'auto_funding_enabled']

class ServiceFallbackSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.get_name_display', read_only=True)
    class Meta: model = ServiceFallback; fields = ["id", "provider", "provider_name", "priority"]

class ServiceRoutingSerializer(serializers.ModelSerializer):
    fallbacks = ServiceFallbackSerializer(source='servicefallback_set', many=True, read_only=True)
    primary_provider_name = serializers.CharField(source='primary_provider.get_name_display', read_only=True)
    class Meta: model = ServiceRouting; fields = ["id", "service", "primary_provider", "primary_provider_name", "fallbacks"]

class VTUProviderOverviewSerializer(serializers.ModelSerializer):
    balance = serializers.FloatField(required=False)
    class Meta:
        model = VTUProviderConfig
        fields = ['id', 'name', 'is_active', 'balance', 'account_name', 'bank_name', 'account_number', 'bank_code', 'min_funding_balance', 'auto_funding_enabled']

class AvailableVTUProviderSerializer(serializers.Serializer):
    id, name = serializers.CharField(), serializers.CharField()
    supported_services = serializers.ListField(child=serializers.CharField(), read_only=True)
    config_requirements = serializers.ListField(child=serializers.DictField(), read_only=True)

class ServiceAutomationConfigSerializer(serializers.ModelSerializer):
    primary_provider_name = serializers.CharField(source='primary_provider.get_name_display', read_only=True)
    class Meta:
        model = ServiceRouting
        fields = ['id', 'service', 'primary_provider', 'primary_provider_name', 'retry_enabled', 'retry_count', 'auto_refund_enabled', 'fallback_enabled', 'pricing_mode', 'customer_margin', 'agent_margin']

class AdminAirtimeNetworkSerializer(serializers.ModelSerializer):
    class Meta: model = AirtimeNetwork; fields = '__all__'

class AdminDataServiceSerializer(serializers.ModelSerializer):
    class Meta: model = DataService; fields = '__all__'

class AdminDataVariationSerializer(serializers.ModelSerializer):
    service_details = AdminDataServiceSerializer(source='service', read_only=True)
    class Meta: model = DataVariation; fields = '__all__'

class AdminTVServiceSerializer(serializers.ModelSerializer):
    class Meta: model = TVService; fields = '__all__'

class AdminTVVariationSerializer(serializers.ModelSerializer):
    service_details = AdminTVServiceSerializer(source='service', read_only=True)
    class Meta: model = TVVariation; fields = '__all__'

class AdminInternetServiceSerializer(serializers.ModelSerializer):
    class Meta: model = InternetService; fields = '__all__'

class AdminInternetVariationSerializer(serializers.ModelSerializer):
    service_details = AdminInternetServiceSerializer(source='service', read_only=True)
    class Meta: model = InternetVariation; fields = '__all__'

class AdminEducationServiceSerializer(serializers.ModelSerializer):
    class Meta: model = EducationService; fields = '__all__'

class AdminEducationVariationSerializer(serializers.ModelSerializer):
    service_details = AdminEducationServiceSerializer(source='service', read_only=True)
    class Meta: model = EducationVariation; fields = '__all__'

class AdminElectricityServiceSerializer(serializers.ModelSerializer):
    class Meta: model = ElectricityService; fields = '__all__'

class AdminElectricityVariationSerializer(serializers.ModelSerializer):
    service_details = AdminElectricityServiceSerializer(source='service', read_only=True)
    class Meta: model = ElectricityVariation; fields = '__all__'
