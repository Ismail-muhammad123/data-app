from django.urls import path

from orders.views import (
        AirtimeNetworkListView, 
        PurchaseAirtimeView, 
        
        DataServicesListView, 
        DataVariationsListView, 
        PurchaseDataVariationView, 
        
        VerifyCustomerView,

        ElectricityServiceListView, 
        PurchaseElectricityView, 
        
        TVServicesListView,
        TVPackagesListView,
        PurchaseTVSubscriptionView,

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
from .webhooks import clubkonnect_callback

urlpatterns = [
    # Status & Callback
    path("purchase-status/<int:pk>/", QueryPurchaseStatusView.as_view(), name="query-purchase-status"),
    path("clubkonnect-callback/", clubkonnect_callback, name="clubkonnect-callback"),

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
    path("buy-electricity/", PurchaseElectricityView.as_view(), name="purchase-electricity"),

    # Cable & TV Subscription Services
    path("tv-services/", TVServicesListView.as_view(), name="list-tv-services"),
    path("tv-packages/", TVPackagesListView.as_view(), name="list-tv-packages"),
    path("buy-tv-subscription/", PurchaseTVSubscriptionView.as_view(), name="purchase-tv-subscription"),

    # Internet Services
    path("internet-packages/", InternetPackagesListView.as_view(), name="list-internet-packages"),
    path("buy-internet-subscription/", PurchaseInternetSubscriptionView.as_view(), name="purchase-internet-subscription"),
    
    # Purchase History
    path("purchase-history/", PurchaseHistoryView.as_view(), name="user-transactions-list"),
    path("purchase-history/<int:pk>/", PurchaseDetailsView.as_view(), name="user-transaction-detail"),
    path("repeat-purchase/", RepeatPurchaseView.as_view(), name="repeat-purchase"),

    # Education Services
    path("education-services/", EducationServiceListView.as_view(), name="list-education-services"),
    path("education-plans/", EducationVariationListView.as_view(), name="list-education-plans"),
    path("buy-education/", PurchaseEducationView.as_view(), name="purchase-education"),

    # Purchase Beneficiaries
    path("beneficiaries/", PurchaseBeneficiaryListCreateView.as_view(), name="purchase-beneficiary-list-create"),
    path("beneficiaries/<int:pk>/", PurchaseBeneficiaryDeleteView.as_view(), name="purchase-beneficiary-delete"),
]
