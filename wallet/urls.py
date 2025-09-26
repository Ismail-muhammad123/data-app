from django.urls import path
from .views import InitFundWalletViaTransferView, WalletDetailView, WalletTransactionListView


urlpatterns = [
    path('', WalletDetailView.as_view(), name='wallet-detail'),
    path('transactions/', WalletTransactionListView.as_view(), name='wallet-transactions'),
    path('deposit/', InitFundWalletViaTransferView.as_view(), name='initiate-deposit'),
    # path('withdraw/', InitiateWithdrawalView.as_view(), name='intiate-withdrawal'),
]
