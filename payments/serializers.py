# payments/serializers.py
from rest_framework import serializers
from .models import Payment



class PaymentCreateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    # Use one of the flows: tokenize (card fields), or charge with authorizationCode
    # Tokenize fields (only when creating token)
    cardNumber = serializers.CharField(required=False, write_only=True)
    expiryMonth = serializers.CharField(required=False, write_only=True)
    expiryYear = serializers.CharField(required=False, write_only=True)
    cvv = serializers.CharField(required=False, write_only=True)
    pin = serializers.CharField(required=False, write_only=True)

    # Metadata
    # fullName = serializers.CharField()
    # email = serializers.EmailField()
    # mobileNumber = serializers.CharField()
    # currency = serializers.CharField(default="NGN")
    # country = serializers.CharField(default="NG")
    # productId = serializers.CharField(default="order_payment")
    # productDescription = serializers.CharField(default="Order payment")
    # paymentReference = serializers.CharField()  # unique ref you create
    # amount = serializers.CharField()

    # Or you can supply an authorizationCode to charge directly:
    # authorizationCode = serializers.CharField(required=False, allow_blank=True)