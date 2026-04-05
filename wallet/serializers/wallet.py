from rest_framework import serializers
from wallet.models import Wallet, VirtualAccount

class VirtualAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualAccount
        fields = "__all__"
        read_only_fields = ["user", "created_at"]

class WalletSerializer(serializers.ModelSerializer):
    virtual_account = serializers.SerializerMethodField()
    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'virtual_account']
    def get_virtual_account(self, obj):
        try:
            va = VirtualAccount.objects.get(user=obj.user)
            return VirtualAccountSerializer(va).data
        except VirtualAccount.DoesNotExist:
            return None
