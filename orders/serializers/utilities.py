from rest_framework import serializers

class VerifyCustomerRequestSerializer(serializers.Serializer):
    service_id = serializers.CharField()
    customer_id = serializers.CharField()
    purchase_type = serializers.ChoiceField(choices=['tv', 'electricity', 'internet'], default='tv')

class VerifyCustomerResponseSerializer(serializers.Serializer):
    account_name = serializers.CharField()
    raw_response = serializers.DictField(required=False)

class RepeatPurchaseRequestSerializer(serializers.Serializer):
    transaction_pin = serializers.CharField(max_length=4, write_only=True)
    purchase_id = serializers.IntegerField()

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()

class SuccessMessageSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()
