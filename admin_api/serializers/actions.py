from rest_framework import serializers

class AdminKYCActionRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False)

class AdminAgentUpgradeRequestSerializer(serializers.Serializer):
    commission_rate = serializers.FloatField(required=False, default=0.0)

class AdminDepositMarkSuccessRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, default="Manually confirmed by Admin")

class AdminWithdrawalActionRequestSerializer(serializers.Serializer):
    pin, reason = serializers.CharField(), serializers.CharField(required=False)

class AdminCreatePurchaseRequestSerializer(serializers.Serializer):
    user_id, purchase_type, amount, beneficiary, action, pin = serializers.IntegerField(), serializers.ChoiceField(choices=['data', 'airtime', 'electricity', 'tv', 'internet', 'education']), serializers.DecimalField(max_digits=10, decimal_places=2), serializers.CharField(), serializers.CharField(), serializers.CharField()
    plan_id, service_id, network_id = serializers.CharField(required=False), serializers.CharField(required=False), serializers.CharField(required=False)

class AdminErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()

class AdminPauseServiceRequestSerializer(serializers.Serializer):
    service, active = serializers.ChoiceField(choices=['airtime', 'data', 'tv', 'electricity', 'education']), serializers.BooleanField()

class AdminStatusResponseSerializer(serializers.Serializer):
    status, message = serializers.CharField(), serializers.CharField()

class AutomationGlobalSettingsSerializer(serializers.Serializer):
    auto_retry_enabled, auto_refund_enabled, notify_admin_on_failure, delayed_tx_detection_enabled = serializers.BooleanField(), serializers.BooleanField(), serializers.BooleanField(), serializers.BooleanField(); delayed_tx_timeout_minutes = serializers.IntegerField(min_value=1)

class VariationPriceUpdateSerializer(serializers.Serializer):
    selling_price, agent_price = serializers.DecimalField(max_digits=10, decimal_places=2), serializers.DecimalField(max_digits=10, decimal_places=2)

class BulkVariationPriceItemSerializer(serializers.Serializer):
    id, selling_price, agent_price = serializers.IntegerField(), serializers.DecimalField(max_digits=10, decimal_places=2), serializers.DecimalField(max_digits=10, decimal_places=2)

class BulkVariationPriceUpdateSerializer(serializers.Serializer):
    variations = BulkVariationPriceItemSerializer(many=True)

class VariationToggleSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()

class ServiceTypeToggleSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()

class ServiceRetryConfigSerializer(serializers.Serializer):
    enabled, count = serializers.BooleanField(), serializers.IntegerField(min_value=0, max_value=10)

class ServicePricingModeSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=['fixed_margin', 'defined']); customer_margin, agent_margin = serializers.DecimalField(max_digits=10, decimal_places=2, required=False), serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

class AdminBeneficiarySerializer(serializers.Serializer):
    class Meta: fields = '__all__' # Placeholder if used, otherwise model serializer needed.
    # Actually I used a ModelSerializer in the original, let me fix it.
