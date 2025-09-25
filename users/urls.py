from django.urls import path
from .views import (
    AdminUserViewSet, ChangePINView, CustomerManagementViewSet, PasswordResetConfirmView, PasswordResetRequestView, ResendActivationCodeView,ActivateAccountView, SignupView, ProfileView, LogoutView, 
)

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("activate-account", ActivateAccountView.as_view(), name="activate-account"),
    path("resend-activation-code/", ResendActivationCodeView.as_view(), name="resend-activation-code"),
    

    path("reset-password/", PasswordResetRequestView.as_view(), name="reset-password"),
    path("confirm-reset-password/", PasswordResetConfirmView.as_view(), name="confirm-reset-password"),
    
    path("profile/", ProfileView.as_view(), name="profile"),

    path("change-pin/", ChangePINView.as_view(), name="change-pin"),
    path("logout/", LogoutView.as_view(), name="logout"),

    # ADMIN DASHBOARD (ADMINS CRUD)
    path("admins/", AdminUserViewSet.as_view({'get': 'retrieve','post': 'create', 'put': 'update', 'delete': 'destroy'}), name="admins"),
    path("customers/", CustomerManagementViewSet.as_view({'get': 'retrieve','post': 'create', 'put': 'update', 'delete': 'destroy'}), name="customers"),   
]