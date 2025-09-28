# vtpass_integration/urls.py
from django.urls import path
# from .views import AllPlanTransactionsView, PlanDetailView, PlanListCreateView, PlanTransactionsByPlanView, PlanTransactionsView, PlansListView, PurchasePlanView


urlpatterns = [
    # Admin
    # path("admin/plans/", PlanListCreateView.as_view(), name="plan-list-create"),
    # path("admin/plans/<int:pk>/", PlanDetailView.as_view(), name="plan-detail"),
    # path("admin/transactions/all/", AllPlanTransactionsView.as_view(), name="all-plan-transactions"),
    # path("admin/transactions/plan/<int:plan_id>/", PlanTransactionsByPlanView.as_view(), name="plan-transactions-by-plan"),


    # # Customer
    # path("list-plans/", PlansListView.as_view(), name="list-plans"),
    # path("purchase/", PurchasePlanView.as_view(), name="purchase-plan"),
    # path("transactions/", PlanTransactionsView.as_view(), name="user-transactions"),

    # Webhook
    # path("webhook/vtpass/", vtpass_webhook, name="vtpass-webhook"),
]