from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema
from wallet.models import Wallet, VirtualAccount
from wallet.serializers import WalletSerializer, VirtualAccountSerializer

class WalletDetailView(generics.RetrieveAPIView):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Wallet"], summary="Get wallet details")
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)
    def get_object(self): return Wallet.objects.get_or_create(user=self.request.user)[0]

class VirtualAccountDetailView(generics.RetrieveAPIView):
    serializer_class = VirtualAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Wallet - Utilities"], summary="Get virtual account details")
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)
    def get_object(self): return VirtualAccount.objects.filter(user=self.request.user).first()
