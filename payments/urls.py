from django.urls import path
from  .views import PaymentListView, PaymentWebhookView

urlpatterns = [
    # ADMIN ENDPOINTS
    path("admin/list-payments/", PaymentListView.as_view(), name="payment-list"),
    # path("create/", PaymentCreateView.as_view(), name="payment-create"),
    # path("update/<str:reference>/", PaymentUpdateView.as_view(), name="payment-update"),

    # APP ENDPOINTS
    path('webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
]