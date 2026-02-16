# vtpass_integration/urls.py
from django.urls import path

from orders.views import (
        # Electricity Services Views
        AirtimeNetworkListView, 
        PurchaseAirtimeView, 
        
        # Data Services Views
        DataServicesListView, 
        DataVariationsListView, 
        PurchaseDataVariationView, 
        
        # Verify Customer View
        VerifyCustomerView,

        # Electricity Services Views
        ElectricityServiceListView, 
        PurchaseElectricityView, 
        
        # TV Services Views
        TVServicesListView,
        TVPackagesListView,
        PurchaseTVSubscriptionView,

        # Smile Services Views
        SmilePackagesListView,
        PurchaseSmileSubscriptionView,

        # Purchase History Views
        PurchaseHistoryView, 
        PurchaseDetailsView 
    )


urlpatterns = [
    # Data Services
    path("data-networks/", DataServicesListView.as_view(), name="list-data-networks"),
    path("data-plans/", DataVariationsListView.as_view(), name="list-plans"),
    path("buy-data/", PurchaseDataVariationView.as_view(), name="purchase-data"),

    # Airtime Services
    path("airtime-networks/", AirtimeNetworkListView.as_view(), name="list-plans"),
    path("buy-airtime/", PurchaseAirtimeView.as_view(), name="purchase-airtime"),

    # Verify Customer
    path("verify-customer/", VerifyCustomerView.as_view(), name="verify-customer"),
    
    # Electricity Services
    path("electricity-services/", ElectricityServiceListView.as_view(), name="list-electricity-services"),
    path("buy-electricity/", PurchaseElectricityView.as_view(), name=" purchase-electricity"),

    # Cable & TV Subscription Services
    path("tv-services/", TVServicesListView.as_view(), name="list-tv-services"),
    path("tv-packages/", TVPackagesListView.as_view(), name="list-tv-packages"),
    path("buy-tv-subscription/", PurchaseTVSubscriptionView.as_view(), name="purchase-tv-subscription"),

    # Smile Services
    path("smile-packages/", SmilePackagesListView.as_view(), name="list-smile-packages"),
    path("buy-smile-subscription/", PurchaseSmileSubscriptionView.as_view(), name="purchase-smile-subscription"),
    
    # Purchase History
    path("purchase-history/", PurchaseHistoryView.as_view(), name="user-transactions"),
    path("purchase-history/<int:pk>", PurchaseDetailsView.as_view(), name="user-transactions"),
]