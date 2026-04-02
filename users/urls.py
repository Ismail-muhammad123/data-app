from django.urls import path
from .views import (
    # Auth
    LoginView,
    RefreshTokenView,
    SignupView,
    ResendActivationCodeView,
    ActivateAccountView,
    LogoutView,
    close_account,
    generate_virtual_account,
    # Profile
    ProfileView,
    # Login PIN
    ChangePINView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    # Transaction PIN
    SetTransactionPinView,
    ChangeTransactionPinView,
    ResetTransactionPinView,
    RequestTransactionPinResetOTPView,
    VerifyTransactionPinView,
    # Referrals
    ReferralListView,
    ReferralStatsView,
    # FCM
    RegisterFCMTokenView,
)

urlpatterns = [
    # ─── Auth ───
    path("signup/", SignupView.as_view(), name="signup"),
    path("activate-account/", ActivateAccountView.as_view(), name="activate-account"),
    path("resend-activation-code/", ResendActivationCodeView.as_view(), name="resend-activation-code"),
    path("login/", LoginView.as_view(), name='login'),
    path("refresh-token/", RefreshTokenView.as_view(), name="refresh-token"),
    path("logout/", LogoutView.as_view(), name="logout"),

    # ─── Profile ───
    path("profile/", ProfileView.as_view(), name="profile"),

    # ─── Login PIN Management ───
    path("change-pin/", ChangePINView.as_view(), name="change-pin"),
    path("reset-password/", PasswordResetRequestView.as_view(), name="reset-password"),
    path("confirm-reset-password/", PasswordResetConfirmView.as_view(), name="confirm-reset-password"),

    # ─── Transaction PIN ───
    path("set-transaction-pin/", SetTransactionPinView.as_view(), name="set-transaction-pin"),
    path("change-transaction-pin/", ChangeTransactionPinView.as_view(), name="change-transaction-pin"),
    path("reset-transaction-pin/", ResetTransactionPinView.as_view(), name="reset-transaction-pin"),
    path("request-transaction-pin-reset/", RequestTransactionPinResetOTPView.as_view(), name="request-transaction-pin-reset"),
    path("verify-transaction-pin/", VerifyTransactionPinView.as_view(), name="verify-transaction-pin"),

    # ─── Referrals ───
    path("referrals/", ReferralListView.as_view(), name="referral-list"),
    path("referral-stats/", ReferralStatsView.as_view(), name="referral-stats"),

    # ─── FCM Token ───
    path("register-fcm-token/", RegisterFCMTokenView.as_view(), name="register-fcm-token"),

    # ─── Account Management ───
    path("close-account/", close_account, name="close-account"),
    path("generate-virtual-account/", generate_virtual_account, name="generate-virtual-account"),
]
