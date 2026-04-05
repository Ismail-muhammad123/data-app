from rest_framework import serializers

class FCMTokenSerializer(serializers.Serializer):
    token = serializers.CharField()
