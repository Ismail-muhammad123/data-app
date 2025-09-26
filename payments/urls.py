from django.urls import path
from  .views import PaymentWebhookView,  InitFundWalletViaTransferView

urlpatterns = [
  
    path('verify-deposit/', InitFundWalletViaTransferView.as_view(), name='verify-deposit'),
    path('webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
]