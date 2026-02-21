from django.urls import path
from  .views import PaymentWebhookView, WithdrawalRequestView, ChargesConfigView

urlpatterns = [
    # ADMIN ENDPOINTS
    # path("admin/list-payments/", PaymentListView.as_view(), name="payment-list"),
    # path("create/", PaymentCreateView.as_view(), name="payment-create"),
    # path("update/<str:reference>/", PaymentUpdateView.as_view(), name="payment-update"),

    # APP ENDPOINTS
    path('webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
    path('withdrawal-request/', WithdrawalRequestView.as_view(), name='withdrawal-request'),
    path('charges-config/', ChargesConfigView.as_view(), name='charges-config'),
]