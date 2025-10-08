# vtpass_integration/urls.py
from django.urls import path

from orders.views import AirtimeNetworkListView, DataNetworksListView, DataPlansListView, PurchaseAirtimeView, PurchaseDataPlanView, PurchaseDetailsView, PurchaseHistoryView
# from .views import AllPlanTransactionsView, PlanDetailView, PlanListCreateView, PlanTransactionsByPlanView, PlanTransactionsView, PlansListView, PurchasePlanView


urlpatterns = [
    # # Customer
    path("data-networks/", DataNetworksListView.as_view(), name="list-data-networks"),
    path("data-plans/", DataPlansListView.as_view(), name="list-plans"),
    path("airtime-networks/", AirtimeNetworkListView.as_view(), name="list-plans"),

    path("buy-data/", PurchaseDataPlanView.as_view(), name="purchase-data"),
    path("buy-airtime/", PurchaseAirtimeView.as_view(), name="purchase-airtime"),
    path("purchase-history/", PurchaseHistoryView.as_view(), name="user-transactions"),
    path("purchase-history/<int:pk>", PurchaseDetailsView.as_view(), name="user-transactions"),
]