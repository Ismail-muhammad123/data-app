from django.urls import path
from .views import InitFundWalletViaTransferView, ManualCreditWalletView, WalletDetailView, WalletTransactionListView, WalletListView, WalletDetailWithTransactionsView


urlpatterns = [
    # ADMIN ENDPOINTS
    path("admin/list-wallets", WalletListView.as_view(), name='admin-list-wallets'),
    path("admin/wallet-details/<int:wallet_id>", WalletDetailWithTransactionsView.as_view(), name='admin-wallet-details'),
    path("admin/credit/", ManualCreditWalletView.as_view(), name='manual-credit'),

    # User API Endpoints
    path('', WalletDetailView.as_view(), name='wallet-detail'),
    path('transactions/', WalletTransactionListView.as_view(), name='wallet-transactions'),
    path('deposit/', InitFundWalletViaTransferView.as_view(), name='initiate-deposit'),
    # path('withdraw/', InitiateWithdrawalView.as_view(), name='intiate-withdrawal'),
]
