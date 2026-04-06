from django.urls import path

from orders.views import (
        AirtimeNetworkListView, 
        PurchaseAirtimeView, 
        
        DataServicesListView, 
        DataVariationsListView, 
        PurchaseDataVariationView, 
        
        VerifyCustomerView,

        ElectricityServiceListView, 
        ElectricityVariationListView,
        PurchaseElectricityView, 
        
        TVServicesListView,
        TVPackagesListView,
        PurchaseTVSubscriptionView,

        InternetServicesListView,
        InternetPackagesListView,
        PurchaseInternetSubscriptionView,

        PurchaseHistoryView, 
        PurchaseDetailsView,
        QueryPurchaseStatusView,
        EducationServiceListView,
        EducationVariationListView, 
        PurchaseEducationView,
        RepeatPurchaseView,
        PurchaseBeneficiaryListCreateView,
        PurchaseBeneficiaryDeleteView
    )
from .webhooks import vtu_webhook, vtu_callback

urlpatterns = [
    # Status & Callback
    path("vtu-status/<int:pk>/", QueryPurchaseStatusView.as_view(), name="query-purchase-status"),
    path("clubkonnect-callback/", vtu_callback, {"provider_name": "clubkonnect"}, name="clubkonnect-callback"),
    path("webhook/<str:provider_name>/", vtu_webhook, name="vtu-webhook"),
    path("callback/<str:provider_name>/", vtu_callback, name="vtu-callback"),

    # Data Services
    path("data-networks/", DataServicesListView.as_view(), name="list-data-networks"),
    path("data-networks/<int:network_id>/plans/", DataVariationsListView.as_view(), name="list-data-plans-by-network"),
    path("data-plans/", DataVariationsListView.as_view(), name="list-plans"),
    path("buy-data/", PurchaseDataVariationView.as_view(), name="purchase-data"),

    # Airtime Services
    path("airtime-networks/", AirtimeNetworkListView.as_view(), name="list-airtime-networks"),
    path("buy-airtime/", PurchaseAirtimeView.as_view(), name="purchase-airtime"),

    # Verify Customer
    path("verify-customer/", VerifyCustomerView.as_view(), name="verify-customer"),
    
    # Electricity Services
    path("electricity-services/", ElectricityServiceListView.as_view(), name="list-electricity-services"),
    path("electricity-services/<int:network_id>/plans/", ElectricityVariationListView.as_view(), name="list-electricity-plans-by-network"),
    path("electricity-plans/", ElectricityVariationListView.as_view(), name="list-electricity-plans"),
    path("buy-electricity/", PurchaseElectricityView.as_view(), name="purchase-electricity"),

    # Cable & TV Subscription Services
    path("tv-services/", TVServicesListView.as_view(), name="list-tv-services"),
    path("tv-services/<int:network_id>/packages/", TVPackagesListView.as_view(), name="list-tv-plans-by-network"),
    path("tv-packages/", TVPackagesListView.as_view(), name="list-tv-packages"),
    path("buy-tv-subscription/", PurchaseTVSubscriptionView.as_view(), name="purchase-tv-subscription"),

    # Internet Services
    path("internet-services/", InternetServicesListView.as_view(), name="list-internet-services"),
    path("internet-services/<int:network_id>/packages/", InternetPackagesListView.as_view(), name="list-internet-plans-by-network"),
    path("internet-packages/", InternetPackagesListView.as_view(), name="list-internet-packages"),
    path("buy-internet-subscription/", PurchaseInternetSubscriptionView.as_view(), name="purchase-internet-subscription"),
    
    # Purchase History
    path("purchase-history/", PurchaseHistoryView.as_view(), name="user-transactions-list"),
    path("purchase-history/<int:pk>/", PurchaseDetailsView.as_view(), name="user-transaction-detail"),
    path("repeat-purchase/", RepeatPurchaseView.as_view(), name="repeat-purchase"),

    # Education Services
    path("education-services/", EducationServiceListView.as_view(), name="list-education-services"),
    path("education-services/<int:network_id>/plans/", EducationVariationListView.as_view(), name="list-education-plans-by-network"),
    path("education-plans/", EducationVariationListView.as_view(), name="list-education-plans"),
    path("buy-education/", PurchaseEducationView.as_view(), name="purchase-education"),

    # Purchase Beneficiaries
    path("beneficiaries/", PurchaseBeneficiaryListCreateView.as_view(), name="purchase-beneficiary-list-create"),
    path("beneficiaries/<int:pk>/", PurchaseBeneficiaryDeleteView.as_view(), name="purchase-beneficiary-delete"),
]
