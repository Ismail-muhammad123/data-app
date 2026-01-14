# vtpass_integration/urls.py
from django.urls import path

from orders.views import AirtimeNetworkListView, DataNetworksListView, DataPlansListView, ElectricityServiceListView, PurchaseAirtimeView, PurchaseDataPlanView, PurchaseDetailsView, PurchaseElectricityView, PurchaseHistoryView, VerifyCustomerView


urlpatterns = [
    # Data Services
    path("data-networks/", DataNetworksListView.as_view(), name="list-data-networks"),
    path("data-plans/", DataPlansListView.as_view(), name="list-plans"),
    path("buy-data/", PurchaseDataPlanView.as_view(), name="purchase-data"),

    # Verify Customer
    path("verify-customer/", VerifyCustomerView.as_view(), name="verify-customer"),

    # Airtime Services
    path("airtime-networks/", AirtimeNetworkListView.as_view(), name="list-plans"),
    path("buy-airtime/", PurchaseAirtimeView.as_view(), name="purchase-airtime"),
    
    # Electricity Services
    path("electricity-services/", ElectricityServiceListView.as_view(), name="list-electricity-services"),
    path("buy-electricity/", PurchaseElectricityView.as_view(), name=" purchase-electricity"),
    
    # Purchase History
    path("purchase-history/", PurchaseHistoryView.as_view(), name="user-transactions"),
    path("purchase-history/<int:pk>", PurchaseDetailsView.as_view(), name="user-transactions"),
]