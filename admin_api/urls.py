from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminDashboardStatsView,
    AdminMaintenanceModeView,
    AdminRefreshServicesView,
    AdminPauseServiceView,
    AdminUserViewSet, 
    AdminWalletTransactionViewSet,
    AdminDepositViewSet,
    AdminWithdrawalViewSet,
    AdminPaystackConfigViewSet,
    AdminPurchaseViewSet,
    AdminSupportTicketViewSet,
    AdminVTUProviderConfigViewSet,
    AdminServiceRoutingViewSet,
    AdminDataVariationViewSet, AdminDataServiceViewSet,
    AdminTVVariationViewSet, AdminTVServiceViewSet,
    AdminAirtimeNetworkViewSet,
    AdminInternetVariationViewSet, AdminInternetServiceViewSet,
    AdminEducationVariationViewSet, AdminEducationServiceViewSet,
    AdminElectricityVariationViewSet, AdminElectricityServiceViewSet,
    AdminBeneficiaryViewSet,
    AdminInitiateTransferView,
    AdminTransferLogView,
    AdminNotificationViewSet,
    AdminAnnouncementViewSet,
    # New Views
    AutomationConfigView, AutomationGlobalSettingsView, ServiceRetryConfigView,
    ServiceFallbackToggleView, ServiceAutoRefundView, ServicePricingModeView,
    DetectDelayedTransactionsView,
    VTUOverviewView, ProviderBalanceView, FetchFromProviderView,
    VariationUpdatePriceView, BulkVariationUpdatePriceView,
    VariationToggleView, ServiceTypeToggleView, AdminAvailableVTUProvidersView
)

router = DefaultRouter()
router.register(r'users', AdminUserViewSet, basename='admin-users')
router.register(r'wallet/transactions', AdminWalletTransactionViewSet, basename='admin-wallet-transactions')
router.register(r'payments/deposits', AdminDepositViewSet, basename='admin-deposits')
router.register(r'payments/withdrawals', AdminWithdrawalViewSet, basename='admin-withdrawals')
router.register(r'settings/paystack', AdminPaystackConfigViewSet, basename='admin-paystack-config')
router.register(r'purchases', AdminPurchaseViewSet, basename='admin-purchases')
router.register(r'support', AdminSupportTicketViewSet, basename='admin-support')
router.register(r'vtu/providers', AdminVTUProviderConfigViewSet, basename='admin-vtu-providers')
router.register(r'vtu/routings', AdminServiceRoutingViewSet, basename='admin-vtu-routings')

router.register(r'pricing/airtime/networks', AdminAirtimeNetworkViewSet, basename='admin-pricing-airtime')
router.register(r'pricing/data/networks', AdminDataServiceViewSet, basename='admin-pricing-data-networks')
router.register(r'pricing/data/plans', AdminDataVariationViewSet, basename='admin-pricing-data-plans')
router.register(r'pricing/tv/networks', AdminTVServiceViewSet, basename='admin-pricing-tv-networks')
router.register(r'pricing/tv/plans', AdminTVVariationViewSet, basename='admin-pricing-tv-plans')
router.register(r'pricing/internet/networks', AdminInternetServiceViewSet, basename='admin-pricing-internet-networks')
router.register(r'pricing/internet/plans', AdminInternetVariationViewSet, basename='admin-pricing-internet-plans')
router.register(r'pricing/education/networks', AdminEducationServiceViewSet, basename='admin-pricing-education-networks')
router.register(r'pricing/education/plans', AdminEducationVariationViewSet, basename='admin-pricing-education-plans')
router.register(r'pricing/electricity/networks', AdminElectricityServiceViewSet, basename='admin-pricing-electricity-networks')
router.register(r'pricing/electricity/plans', AdminElectricityVariationViewSet, basename='admin-pricing-electricity-plans')

router.register(r'transfer/beneficiaries', AdminBeneficiaryViewSet, basename='admin-transfer-beneficiaries')
router.register(r'notifications', AdminNotificationViewSet, basename='admin-notifications')
router.register(r'notifications/announcements', AdminAnnouncementViewSet, basename='admin-announcements')

urlpatterns = [
    path('stats/', AdminDashboardStatsView.as_view(), name='admin-stats'),
    path('vtu/available-providers/', AdminAvailableVTUProvidersView.as_view(), name='admin-vtu-available-providers'),
    path('maintenance-mode/', AdminMaintenanceModeView.as_view(), name='admin-maintenance-mode'),
    path('refresh-services/', AdminRefreshServicesView.as_view(), name='admin-refresh-services'),
    path('pause-service/', AdminPauseServiceView.as_view(), name='admin-pause-service'),
    path('transfer/initiate/', AdminInitiateTransferView.as_view(), name='admin-transfer-initiate'),
    path('transfer/logs/', AdminTransferLogView.as_view(), name='admin-transfer-logs'),
    
    # Automation
    path('automation/config/', AutomationConfigView.as_view(), name='admin-automation-config'),
    path('automation/global-settings/', AutomationGlobalSettingsView.as_view(), name='admin-automation-global'),
    path('automation/service/<str:service>/retry/', ServiceRetryConfigView.as_view(), name='admin-service-retry'),
    path('automation/service/<str:service>/fallback/', ServiceFallbackToggleView.as_view(), name='admin-service-fallback'),
    path('automation/service/<str:service>/auto-refund/', ServiceAutoRefundView.as_view(), name='admin-service-auto-refund'),
    path('automation/service/<str:service>/pricing-mode/', ServicePricingModeView.as_view(), name='admin-service-pricing-mode'),
    path('automation/detect-delayed/', DetectDelayedTransactionsView.as_view(), name='admin-detect-delayed'),

    # VTU Control Panel
    path('vtu/overview/', VTUOverviewView.as_view(), name='admin-vtu-overview'),
    path('vtu/providers/<int:pk>/balance/', ProviderBalanceView.as_view(), name='admin-provider-balance'),
    path('vtu/fetch-from-provider/', FetchFromProviderView.as_view(), name='admin-vtu-fetch'),
    path('vtu/variations/<int:pk>/update-price/<str:service_type>/', VariationUpdatePriceView.as_view(), name='admin-vtu-variation-price'),
    path('vtu/variations/bulk-update-price/<str:service_type>/', BulkVariationUpdatePriceView.as_view(), name='admin-vtu-bulk-price'),
    path('vtu/variations/<int:pk>/toggle/<str:service_type>/', VariationToggleView.as_view(), name='admin-vtu-variation-toggle'),
    path('vtu/services/<str:service_type>/toggle/', ServiceTypeToggleView.as_view(), name='admin-vtu-service-toggle'),

    path('', include(router.urls)),
]
