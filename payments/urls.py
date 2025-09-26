from django.urls import path
from  .views import PaymentWebhookView,  InitFundWalletViaTransferView

urlpatterns = [
    path('webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
]