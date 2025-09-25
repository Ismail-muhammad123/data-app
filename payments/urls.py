# payments/urls.py
from django.urls import path

from .views import PaymentCallbackView, PaymentInitView

urlpatterns = [
    path("init/<int:order_id>/", PaymentInitView.as_view(), name="payment-init"),
    path("callback/", PaymentCallbackView.as_view(), name="payment-callback"),
]
