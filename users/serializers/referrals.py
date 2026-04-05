from rest_framework import serializers
from users.models import Referral

class ReferralSerializer(serializers.ModelSerializer):
    referred_phone = serializers.CharField(source='referred.phone_number', read_only=True)
    referred_name = serializers.CharField(source='referred.full_name', read_only=True)

    class Meta:
        model = Referral
        fields = ['id', 'referred_phone', 'referred_name', 'bonus_paid', 'bonus_amount', 'created_at']
        read_only_fields = fields
