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
    AdminPurchaseViewSet,
    AdminSupportTicketViewSet,
    AdminVTUProviderConfigViewSet,
    AdminServiceRoutingViewSet,
    AdminDataVariationViewSet,
    AdminTVVariationViewSet,
    AdminAirtimeNetworkViewSet,
    AdminSmileVariationViewSet,
    AdminEducationVariationViewSet,
    AdminElectricityVariationViewSet,
    AdminPromoCodeViewSet,
    AdminBeneficiaryViewSet,
    AdminInitiateTransferView,
    AdminTransferLogView,
    AdminNotificationLogViewSet,
    AdminAnnouncementViewSet,
    AdminNotificationProviderConfigViewSet
)

router = DefaultRouter()
router.register(r'users', AdminUserViewSet, basename='admin-users')
router.register(r'wallet/transactions', AdminWalletTransactionViewSet, basename='admin-wallet-transactions')
router.register(r'payments/deposits', AdminDepositViewSet, basename='admin-deposits')
router.register(r'payments/withdrawals', AdminWithdrawalViewSet, basename='admin-withdrawals')
router.register(r'purchases', AdminPurchaseViewSet, basename='admin-purchases')
router.register(r'support', AdminSupportTicketViewSet, basename='admin-support')
router.register(r'vtu/providers', AdminVTUProviderConfigViewSet, basename='admin-vtu-providers')
router.register(r'vtu/routings', AdminServiceRoutingViewSet, basename='admin-vtu-routings')
router.register(r'pricing/data', AdminDataVariationViewSet, basename='admin-pricing-data')
router.register(r'pricing/tv', AdminTVVariationViewSet, basename='admin-pricing-tv')
router.register(r'pricing/airtime', AdminAirtimeNetworkViewSet, basename='admin-pricing-airtime')
router.register(r'pricing/smile', AdminSmileVariationViewSet, basename='admin-pricing-smile')
router.register(r'pricing/education', AdminEducationVariationViewSet, basename='admin-pricing-education')
router.register(r'pricing/electricity', AdminElectricityVariationViewSet, basename='admin-pricing-electricity')
router.register(r'pricing/promos', AdminPromoCodeViewSet, basename='admin-pricing-promos')
router.register(r'transfer/beneficiaries', AdminBeneficiaryViewSet, basename='admin-transfer-beneficiaries')
router.register(r'notifications/logs', AdminNotificationLogViewSet, basename='admin-notifications-logs')
router.register(r'notifications/announcements', AdminAnnouncementViewSet, basename='admin-announcements')
router.register(r'notifications/providers', AdminNotificationProviderConfigViewSet, basename='admin-notification-providers')

urlpatterns = [
    path('stats/', AdminDashboardStatsView.as_view(), name='admin-stats'),
    path('maintenance-mode/', AdminMaintenanceModeView.as_view(), name='admin-maintenance-mode'),
    path('refresh-services/', AdminRefreshServicesView.as_view(), name='admin-refresh-services'),
    path('pause-service/', AdminPauseServiceView.as_view(), name='admin-pause-service'),
    path('transfer/initiate/', AdminInitiateTransferView.as_view(), name='admin-transfer-initiate'),
    path('transfer/logs/', AdminTransferLogView.as_view(), name='admin-transfer-logs'),
    path('', include(router.urls)),
]
