from rest_framework import serializers
from .models import SupportTicket, TicketMessage

class TicketMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.phone_number', read_only=True)

    class Meta:
        model = TicketMessage
        fields = ['id', 'sender_name', 'message', 'is_admin', 'created_at']

class SupportTicketSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)

    class Meta:
        model = SupportTicket
        fields = ['id', 'subject', 'description', 'category', 'status', 'related_reference', 'created_at', 'updated_at', 'messages']
        read_only_fields = ['status', 'created_at', 'updated_at']
