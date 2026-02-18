from django.urls import path
from .views import (
    InitFundWallet, WalletDetailView, WalletTransactionDetailView, 
    WalletTransactionListView, VirtualAccountDetailView, BankListView, 
    ResolveAccountView, WithdrawalAccountDetailView
)


urlpatterns = [
    # ADMIN ENDPOINTS
    # path("admin/list-wallets", WalletListView.as_view(), name='admin-list-wallets'),
    # path("admin/wallet-details/<int:wallet_id>", WalletDetailWithTransactionsView.as_view(), name='admin-wallet-details'),
    # path("admin/credit/", ManualCreditWalletView.as_view(), name='manual-credit'),

    # User API Endpoints
    path('', WalletDetailView.as_view(), name='wallet-detail'),
    path('transactions/', WalletTransactionListView.as_view(), name='wallet-transactions'),
    path('transactions/<int:pk>/', WalletTransactionDetailView.as_view(), name='wallet-transaction-detail'),
    path('deposit/', InitFundWallet.as_view(), name='initiate-deposit'),
    path('virtual-account/', VirtualAccountDetailView.as_view(), name='virtual-account'),
    path('banks/', BankListView.as_view(), name='bank-list'),
    path('resolve-account/', ResolveAccountView.as_view(), name='resolve-account'),
    path('withdrawal-account/', WithdrawalAccountDetailView.as_view(), name='withdrawal-account'),

    # path('withdraw/', InitiateWithdrawalView.as_view(), name='intiate-withdrawal'),
]
