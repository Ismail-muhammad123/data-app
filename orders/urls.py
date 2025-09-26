# vtpass_integration/urls.py
from django.urls import path
from .views import PlanDetailView, PlanListCreateView, PlanTransactionsView, PlansListView, PurchasePlanView


urlpatterns = [
    # Admin
    path("plans/", PlanListCreateView.as_view(), name="plan-list-create"),
    path("plans/<int:pk>/", PlanDetailView.as_view(), name="plan-detail"),

    # Customer
    path("list-plans/", PlansListView.as_view(), name="list-plans"),
    path("purchase/", PurchasePlanView.as_view(), name="purchase-plan"),
    path("transactions/", PlanTransactionsView.as_view(), name="user-transactions"),

    # Webhook
    # path("webhook/vtpass/", vtpass_webhook, name="vtpass-webhook"),
]