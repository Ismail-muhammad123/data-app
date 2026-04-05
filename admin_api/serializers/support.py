from rest_framework import serializers
from support.models import SupportTicket, TicketMessage

class AdminTicketMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.phone_number', read_only=True)
    class Meta: model = TicketMessage; fields = '__all__'

class AdminSupportTicketSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone_number', read_only=True); messages = AdminTicketMessageSerializer(many=True, read_only=True)
    class Meta: model = SupportTicket; fields = '__all__'

class AdminSupportReplyRequestSerializer(serializers.Serializer):
    message = serializers.CharField()
