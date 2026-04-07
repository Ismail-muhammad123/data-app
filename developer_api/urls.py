from django.urls import path
from .views.auth import UpgradeToDeveloperView, DeveloperDetailsView, RegenerateAPIKeyView
from .views.services import DeveloperServiceListView, DeveloperAirtimeNetworkListView, DeveloperDataNetworkListView, DeveloperDataPlanListView, DeveloperTVServiceListView, DeveloperTVPackageListView
from .views.purchase import DeveloperPurchaseView, DeveloperVerifyPurchaseView

urlpatterns = [
    # Auth & Account
    path('upgrade/', UpgradeToDeveloperView.as_view(), name='developer-upgrade'),
    path('profile/', DeveloperDetailsView.as_view(), name='developer-profile'),
    path('keys/regenerate/', RegenerateAPIKeyView.as_view(), name='developer-keys-regenerate'),
    
    # Discovery
    path('services/', DeveloperServiceListView.as_view(), name='developer-service-list'),
    path('airtime/networks/', DeveloperAirtimeNetworkListView.as_view(), name='developer-airtime-networks'),
    path('data/networks/', DeveloperDataNetworkListView.as_view(), name='developer-data-networks'),
    path('data/networks/<int:network_id>/plans/', DeveloperDataPlanListView.as_view(), name='developer-data-plans'),
    path('tv/services/', DeveloperTVServiceListView.as_view(), name='developer-tv-services'),
    path('tv/services/<int:service_id>/packages/', DeveloperTVPackageListView.as_view(), name='developer-tv-packages'),
    
    # Transactions
    path('purchase/', DeveloperPurchaseView.as_view(), name='developer-purchase'),
    path('verify/<str:reference>/', DeveloperVerifyPurchaseView.as_view(), name='developer-verify'),
]
