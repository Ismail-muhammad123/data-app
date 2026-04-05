from django.urls import path
from .views import (
    SignupView, ActivateAccountView, ResendActivationCodeView, LoginView, RefreshTokenView, 
    GoogleAuthView, Verify2FAView, LogoutView, PasswordResetRequestView, PasswordResetConfirmView, 
    ProfileView, ChangePINView, close_account, generate_virtual_account, Update2FASettingsView, 
    SetTransactionPinView, ChangeTransactionPinView, ResetTransactionPinView, 
    RequestTransactionPinResetOTPView, VerifyTransactionPinView, NotificationListView, 
    MarkNotificationReadView, MarkAllNotificationsReadView, ReferralListView, 
    ReferralStatsView, RegisterFCMTokenView
)

urlpatterns = [
    # ═══════════════════════════════════════════
    # AUTH  (public – no token required)
    # ═══════════════════════════════════════════
    path("signup/", SignupView.as_view(), name="signup"),
    path("activate-account/", ActivateAccountView.as_view(), name="activate-account"),
    path("resend-activation-code/", ResendActivationCodeView.as_view(), name="resend-activation-code"),
    path("login/", LoginView.as_view(), name='login'),
    path("refresh-token/", RefreshTokenView.as_view(), name="refresh-token"),
    path("google/", GoogleAuthView.as_view(), name="google-auth"),
    path("verify-2fa/", Verify2FAView.as_view(), name="verify-2fa"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("reset-password/", PasswordResetRequestView.as_view(), name="reset-password"),
    path("confirm-reset-password/", PasswordResetConfirmView.as_view(), name="confirm-reset-password"),

    # ═══════════════════════════════════════════
    # PROFILE  (authenticated)
    # ═══════════════════════════════════════════
    path("profile/", ProfileView.as_view(), name="profile"),
    path("change-pin/", ChangePINView.as_view(), name="change-pin"),
    path("close-account/", close_account, name="close-account"),
    path("generate-virtual-account/", generate_virtual_account, name="generate-virtual-account"),

    # ═══════════════════════════════════════════
    # TWO-FACTOR AUTHENTICATION  (authenticated)
    # ═══════════════════════════════════════════
    path("2fa/settings/", Update2FASettingsView.as_view(), name="update-2fa-settings"),

    # ═══════════════════════════════════════════
    # TRANSACTION PIN  (authenticated)
    # ═══════════════════════════════════════════
    path("set-transaction-pin/", SetTransactionPinView.as_view(), name="set-transaction-pin"),
    path("change-transaction-pin/", ChangeTransactionPinView.as_view(), name="change-transaction-pin"),
    path("reset-transaction-pin/", ResetTransactionPinView.as_view(), name="reset-transaction-pin"),
    path("request-transaction-pin-reset-otp/", RequestTransactionPinResetOTPView.as_view(), name="request-transaction-pin-reset"),
    path("verify-transaction-pin/", VerifyTransactionPinView.as_view(), name="verify-transaction-pin"),

    # ═══════════════════════════════════════════
    # NOTIFICATIONS  (authenticated)
    # ═══════════════════════════════════════════
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path("notifications/<int:notification_id>/mark-as-read/", MarkNotificationReadView.as_view(), name="notification-mark-read"),
    path("notifications/mark-all-as-read/", MarkAllNotificationsReadView.as_view(), name="notification-mark-all-read"),

    # ═══════════════════════════════════════════
    # REFERRALS  (authenticated)
    # ═══════════════════════════════════════════
    path("referrals/", ReferralListView.as_view(), name="referral-list"),
    path("referrals/stats/", ReferralStatsView.as_view(), name="referral-stats"),

    # ═══════════════════════════════════════════
    # DEVICE / FCM  (authenticated)
    # ═══════════════════════════════════════════
    path("device/register-fcm-token/", RegisterFCMTokenView.as_view(), name="register-fcm-token"),
]
