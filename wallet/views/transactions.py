from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema
from wallet.models import Wallet
from wallet.serializers import WalletTransactionSerializer

class WalletTransactionListView(generics.ListAPIView):
    serializer_class = WalletTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Wallet"], summary="List wallet transactions")
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)
    def get_queryset(self): return Wallet.objects.get_or_create(user=self.request.user)[0].transactions.all().order_by('-timestamp')

class WalletTransactionDetailView(generics.RetrieveAPIView):
    serializer_class = WalletTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Wallet"], summary="Get wallet transaction details")
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)
    def get_object(self):
        wallet = Wallet.objects.get_or_create(user=self.request.user)[0]
        return generics.get_object_or_404(wallet.transactions, pk=self.kwargs.get('pk'))
