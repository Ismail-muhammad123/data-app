from django.urls import path
from .views import (
    SignupView, ResetPasswordView, ProfileView,
    UpdateProfileView, ChangePasswordView, LogoutView
)

urlpatterns = [
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("auth/profile/", ProfileView.as_view(), name="get-profile"),
    path("auth/update-profile/", UpdateProfileView.as_view(), name="update-profile"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
]