# users/views.py
from django.contrib.auth import get_user_model, logout, authenticate
from rest_framework import status, generics, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample, inline_serializer, extend_schema_view
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .models import OTP, Referral, Beneficiary
from .utils import send_otp_code
from notifications.models import UserNotification
from .serializers import (
    ChangeTransactionPinSerializer,
    FCMTokenSerializer,
    LoginSerializer,
    PasswordResetSerializer,
    ProfileSerializer,
    ReferralSerializer,
    ResetTransactionPinSerializer,
    SetTransactionPinSerializer,
    SignupSerializer,
    UpdateProfileSerializer,
    VerifyTransactionPinSerializer,
    UserNotificationSerializer,
    ChangePINSerializer,
    GoogleAuthSerializer,
    Verify2FASerializer,
)
from django.conf import settings
from django.db.models import Sum

from rest_framework.decorators import api_view, permission_classes
from wallet.models import VirtualAccount
from wallet.serializers import VirtualAccountSerializer
from payments.utils import PaystackGateway


User = get_user_model()


# ──────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────

class LoginView(APIView):
    """Login with phone number and PIN"""


    @extend_schema(
        tags=["Account - Auth"],
        request=LoginSerializer,
        examples=[
            OpenApiExample(
                "Valid Login",
                value={"phone_number": "08012345678", "pin": "1234"},
                request_only=True
            )
        ],
        responses={
            200: inline_serializer(
                name="LoginResponse",
                fields={
                    "refresh": serializers.CharField(),
                    "access": serializers.CharField(),
                    "user": ProfileSerializer()
                }
            )
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone_number"]
        pin = serializer.validated_data["pin"]

        user = authenticate(username=phone, password=pin)
        if not user:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            # Check if user exists and needs activation
            temp_user = User.objects.get(phone_number=phone)
            if not temp_user.is_verified:
                 return Response({"error": "Account not verified", "code": "ACCOUNT_NOT_VERIFIED"}, status=status.HTTP_403_FORBIDDEN)
            return Response({"error": "Account not active"}, status=status.HTTP_403_FORBIDDEN)

        # Check for 2FA
        from summary.models import SiteConfig
        config = SiteConfig.objects.first()
        is_staff_enforced = user.is_staff and config and config.enforce_2fa_for_staff
        
        if is_staff_enforced or user.is_2fa_enabled:
            send_otp_code(user, "2fa")
            return Response({
                "two_factor_required": True,
                "message": "A 2FA code has been sent to your registered channels.",
                "identifier": user.phone_number
            }, status=status.HTTP_200_OK)

        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": ProfileSerializer(user).data
        })


class RefreshTokenView(APIView):
    """Obtain a new access token using a refresh token."""
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Account - Auth"],
        request=inline_serializer("RefreshTokenRequest", fields={"refresh": serializers.CharField()}),
        examples=[
            OpenApiExample(
                "Refresh Token",
                value={"refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."},
                request_only=True
            )
        ],
        responses={
            200: inline_serializer("RefreshTokenResponse", fields={"access": serializers.CharField()})
        }
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            return Response({"access": access_token}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)


class GoogleAuthView(APIView):
    """Sign up or sign in with Google ID token"""
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Account - Auth"],
        request=GoogleAuthSerializer,
        responses={200: inline_serializer("GoogleAuthResponse", fields={"refresh": serializers.CharField(), "access": serializers.CharField(), "user": ProfileSerializer()})}
    )
    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["id_token"]
        phone_number = serializer.validated_data.get("phone_number")
        referral_code = serializer.validated_data.get("referral_code")

        try:
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
            email = idinfo['email']
            google_id = idinfo['sub']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            
            # Find or create user
            user = User.objects.filter(google_id=google_id).first()
            if not user:
                user = User.objects.filter(email=email).first()
                if user:
                    user.google_id = google_id
                    user.save(update_fields=['google_id'])
                else:
                    # New user
                    if not phone_number:
                        return Response({
                            "error": "Google account not linked to any existing user. Please provide phone number to complete signup.",
                            "code": "PHONE_NUMBER_REQUIRED",
                            "google_data": {
                                "email": email,
                                "first_name": first_name,
                                "last_name": last_name,
                                "google_id": google_id
                            }
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Create user
                    user = User.objects.create_user(
                        phone_number=phone_number,
                        email=email,
                        google_id=google_id,
                        first_name=first_name,
                        last_name=last_name,
                        is_active=True,
                        email_verified=True,
                    )
                    user.is_verified = True
                    user.save()
                    
                    # Handle referral if any
                    if referral_code:
                        try:
                            referrer = User.objects.get(referral_code=referral_code)
                            from .models import Referral
                            Referral.objects.create(referrer=referrer, referred=user)
                        except User.DoesNotExist:
                            pass

            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": ProfileSerializer(user).data
            })
        except ValueError:
            return Response({"error": "Invalid Google token"}, status=status.HTTP_400_BAD_REQUEST)


class Verify2FAView(APIView):
    """Verify 2FA code and complete login"""
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Account - 2FA"],
        request=Verify2FASerializer,
        responses={200: inline_serializer("Verify2FAResponse", fields={"refresh": serializers.CharField(), "access": serializers.CharField(), "user": ProfileSerializer()})}
    )
    def post(self, request):
        serializer = Verify2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data["identifier"]
        otp_code = serializer.validated_data["otp_code"]

        try:
            if "@" in identifier:
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(phone_number=identifier)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            otp = OTP.objects.get(user=user, code=otp_code, purpose="2fa", is_used=False)
        except OTP.DoesNotExist:
            return Response({"error": "Invalid or expired 2FA code"}, status=status.HTTP_400_BAD_REQUEST)

        # Mark OTP as used
        otp.is_used = True
        otp.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": ProfileSerializer(user).data
        })


@extend_schema(
    tags=["Account - Auth"],
    request=SignupSerializer,
    examples=[
        OpenApiExample(
            "Signup Request",
            value={
                "phone_country_code": "+234",
                "phone_number": "08012345678",
                "email": "user@example.com",
                "pin": "1234",
                "first_name": "John",
                "last_name": "Doe"
            },
            request_only=True
        )
    ],
    responses={201: SignupSerializer}
)
class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignupSerializer

    def perform_create(self, serializer):
        user = serializer.save(is_active=True)  # wait for OTP verification
        # send_otp_code(user, "activation")


class ResendActivationCodeView(APIView):
    @extend_schema(
        tags=["Account - Auth"],
        request=inline_serializer("ResendActivationCodeRequest", fields={
            "identifier": serializers.CharField(),
            "channel": serializers.CharField(required=False)
        }),
        examples=[
            OpenApiExample(
                "Resend via SMS",
                value={"identifier": "08012345678", "channel": "sms"},
                request_only=True
            )
        ],
        responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})}
    )
    def post(self, request):
        identifier = request.data.get("identifier")
        channel = request.data.get("channel", None)

        if not identifier:
            return Response({"error": "Phone Number is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(phone_number=identifier)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_verified:
            return Response({"error": "Account is already verified."}, status=status.HTTP_400_BAD_REQUEST)

        send_otp_code(user, "activation", preferred_channel=channel)
        return Response({"message": "Activation code resent successfully."}, status=status.HTTP_200_OK)


class ActivateAccountView(APIView):
    @extend_schema(
        tags=["Account - Auth"],
        request=inline_serializer("ActivateAccountRequest", fields={"identifier": serializers.CharField(), "otp": serializers.CharField()}),
        examples=[
            OpenApiExample(
                "Activate Account",
                value={"identifier": "08012345678", "otp": "123456"},
                request_only=True
            )
        ],
        responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})}
    )
    def post(self, request):
        identifier = request.data.get("identifier")
        otp_code = request.data.get("otp")

        if not identifier or not otp_code:
            return Response({"error": "Phone Number and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(phone_number=identifier)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            otp = OTP.objects.get(user=user, code=otp_code, purpose="activation", is_used=False)
        except OTP.DoesNotExist:
            return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.is_verified = True
        if otp.channel == "email":
            user.email_verified = True
        elif otp.channel in ["sms", "whatsapp"]:
            user.phone_number_verified = True
        user.save()
        otp.is_used = True
        otp.save()

        # Site Configuration Logic: Signup Bonus & Referral Reward
        from summary.models import SiteConfig
        from wallet.utils import fund_wallet, process_referral_reward
        
        config = SiteConfig.objects.first()
        if config and config.signup_bonus_enabled and config.signup_bonus_amount > 0:
            fund_wallet(user.id, float(config.signup_bonus_amount), description="Signup Bonus", initiator='system')
        
        # Referral commission on signup
        process_referral_reward(user, trigger_event='signup')

        return Response({"message": "Account activated successfully."}, status=status.HTTP_200_OK)


# ──────────────────────────────────────────────
# Profile
# ──────────────────────────────────────────────

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Account - Profile"],
        responses={200: ProfileSerializer}
    )
    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        tags=["Account - Profile"],
        request=UpdateProfileSerializer,
        examples=[
            OpenApiExample(
                "Update Profile",
                value={"first_name": "Jane", "last_name": "Doe", "email": "jane@example.com"},
                request_only=True
            )
        ],
        responses={200: UpdateProfileSerializer}
    )
    def post(self, request):
        if request.user.email and request.data.get("email") and request.user.email != request.data.get("email"):
            users = User.objects.filter(email=request.data.get("email"), email_verified=True).exclude(id=request.user.id)
            if users.exists():
                return Response({"error": "Email already in use."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class Update2FASettingsView(APIView):
    """Update 2FA settings for the current user"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Account - 2FA"],
        request=inline_serializer("Update2FAStatusRequest", fields={
            "is_2fa_enabled": serializers.BooleanField(),
            "two_factor_method": serializers.ChoiceField(choices=User.TWO_FACTOR_METHODS)
        }),
        responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})}
    )
    def post(self, request):
        is_enabled = request.data.get("is_2fa_enabled")
        method = request.data.get("two_factor_method")

        if is_enabled is not None:
            request.user.is_2fa_enabled = is_enabled
        if method:
            request.user.two_factor_method = method
        
        request.user.save()
        return Response({"message": "2FA settings updated successfully."})

# ──────────────────────────────────────────────
# Login PIN Management
# ──────────────────────────────────────────────

class PasswordResetRequestView(APIView):
    @extend_schema(
        tags=["Account - Auth"],
        request=inline_serializer("PasswordResetRequest", fields={"identifier": serializers.CharField()}),
        examples=[
            OpenApiExample(
                "Request Reset",
                value={"identifier": "08012345678"},
                request_only=True
            )
        ],
        responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})}
    )
    def post(self, request):
        identifier = request.data.get("identifier")
        identifier = identifier[1:] if identifier and identifier.startswith("0") else identifier

        try:
            user = User.objects.get(phone_number=identifier)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        send_otp_code(user, "reset")
        return Response({"message": "OTP sent for password reset"})


class PasswordResetConfirmView(APIView):
    @extend_schema(
        tags=["Account - Auth"],
        request=PasswordResetSerializer,
        examples=[
            OpenApiExample(
                "Confirm Reset",
                value={"identifier": "08012345678", "otp_code": "123456", "new_pin": "5678"},
                request_only=True
            )
        ],
        responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})}
    )
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "PIN reset successful"})

class ChangePINView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Account - Profile"],
        request=ChangePINSerializer,
        examples=[
            OpenApiExample(
                "Change Login PIN",
                value={"old_pin": "1234", "new_pin": "5678"},
                request_only=True
            )
        ],
        responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})}
    )
    def post(self, request):
        serializer = ChangePINSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "PIN changed successfully"})

# ──────────────────────────────────────────────
# Transaction PIN Management
# ──────────────────────────────────────────────

class SetTransactionPinView(APIView):
    """Set the transaction PIN for the first time."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Account - Transaction PIN"],
        request=SetTransactionPinSerializer,
        examples=[
            OpenApiExample(
                "Set Transaction PIN",
                value={"pin": "1234", "confirm_pin": "1234"},
                request_only=True
            )
        ],
        responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})}
    )
    def post(self, request):
        serializer = SetTransactionPinSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_transaction_pin(serializer.validated_data['pin'])
        return Response({"message": "Transaction PIN set successfully."})


class ChangeTransactionPinView(APIView):
    """Change existing transaction PIN."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Account - Transaction PIN"],
        request=ChangeTransactionPinSerializer,
        examples=[
            OpenApiExample(
                "Change Transaction PIN",
                value={"old_pin": "1234", "new_pin": "5678", "confirm_pin": "5678"},
                request_only=True
            )
        ],
        responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})}
    )
    def post(self, request):
        serializer = ChangeTransactionPinSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_transaction_pin(serializer.validated_data['new_pin'])
        return Response({"message": "Transaction PIN changed successfully."})


class ResetTransactionPinView(APIView):
    """Reset transaction PIN via OTP (requires OTP to be requested first)."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Account - Transaction PIN"],
        request=ResetTransactionPinSerializer,
        examples=[
            OpenApiExample(
                "Reset Transaction PIN",
                value={"otp_code": "123456", "new_pin": "5678", "confirm_pin": "5678"},
                request_only=True
            )
        ],
        responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})}
    )
    def post(self, request):
        serializer = ResetTransactionPinSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        # Mark OTP as used
        OTP.objects.filter(
            user=request.user,
            code=serializer.validated_data['otp_code'],
            purpose='reset',
            is_used=False
        ).update(is_used=True)
        request.user.set_transaction_pin(serializer.validated_data['new_pin'])
        return Response({"message": "Transaction PIN reset successfully."})

class RequestTransactionPinResetOTPView(APIView):
    """Request an OTP to reset the transaction PIN."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Account - Transaction PIN"],
        request=None,
        responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})}
    )
    def post(self, request):
        send_otp_code(request.user, "reset")
        return Response({"message": "OTP sent for transaction PIN reset."})


class VerifyTransactionPinView(APIView):
    """Verify if a transaction PIN is correct."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Account - Transaction PIN"],
        request=VerifyTransactionPinSerializer,
        examples=[
            OpenApiExample(
                "Verify Transaction PIN",
                value={"pin": "1234"},
                request_only=True
            )
        ],
        responses={200: inline_serializer("VerifyPinResponse", fields={"valid": serializers.BooleanField()})}
    )
    def post(self, request):
        serializer = VerifyTransactionPinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_valid = request.user.check_transaction_pin(serializer.validated_data['pin'])
        return Response({"valid": is_valid})


# ──────────────────────────────────────────────
# Referral System
# ──────────────────────────────────────────────

@extend_schema(tags=["Account - Referrals"])
class ReferralListView(generics.ListAPIView):
    """List all users referred by the current user."""
    serializer_class = ReferralSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Referral.objects.filter(referrer=self.request.user)


class ReferralStatsView(APIView):
    """Get referral statistics for the current user."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Account - Referrals"],
        responses={
            200: inline_serializer(
                "ReferralStatsResponse",
                fields={
                    "referral_code": serializers.CharField(),
                    "total_referrals": serializers.IntegerField(),
                    "total_bonus_earned": serializers.FloatField()
                }
            )
        }
    )
    def get(self, request):
        referrals = Referral.objects.filter(referrer=request.user)
        total_referrals = referrals.count()
        total_bonus = referrals.aggregate(total=Sum('bonus_amount'))['total'] or 0

        return Response({
            "referral_code": request.user.referral_code,
            "total_referrals": total_referrals,
            "total_bonus_earned": float(total_bonus),
        })




# ──────────────────────────────────────────────
# FCM Token
# ──────────────────────────────────────────────

@extend_schema(
    tags=["Account - Notifications"],
    request=FCMTokenSerializer,
    examples=[
        OpenApiExample(
            "Register FCM Token",
            value={"token": "bk3RNwTe3H0:CI2k_HHwgIpoDKCIZvvDMExUdFQ3P1..."},
            request_only=True
        )
    ],
    responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})}
)
class RegisterFCMTokenView(APIView):
    """Register or update FCM device token for push notifications."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = FCMTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.fcm_token = serializer.validated_data['token']
        request.user.save(update_fields=['fcm_token'])
        return Response({"message": "FCM token registered successfully."})

from django.utils import timezone


@extend_schema(tags=["Account - Notifications"])
class NotificationListView(generics.ListAPIView):
    """List all notifications for the current user."""
    serializer_class = UserNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserNotification.objects.filter(user=self.request.user).order_by('-created_at')


@extend_schema(
    tags=["Account - Notifications"],
    request=None,
    responses={200: inline_serializer("MarkReadResponse", fields={"message": serializers.CharField()})}
)
class MarkNotificationReadView(APIView):
    """Mark a single notification as read."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, notification_id):
        updated = UserNotification.objects.filter(
            user=request.user, id=notification_id
        ).update(is_read=True, read_at=timezone.now())

        if not updated:
            return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "Notification marked as read"})


@extend_schema(
    tags=["Account - Notifications"],
    request=None,
    responses={200: inline_serializer("MarkAllReadResponse", fields={"message": serializers.CharField()})}
)
class MarkAllNotificationsReadView(APIView):
    """Mark all notifications as read for the current user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        count = UserNotification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return Response({"message": f"{count} notifications marked as read"})


# ──────────────────────────────────────────────
# Account Management
# ──────────────────────────────────────────────

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Account - Auth"],
        request=inline_serializer("LogoutRequest", fields={"refresh": serializers.CharField()}),
        examples=[
            OpenApiExample(
                "Logout Request",
                value={"refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."},
                request_only=True
            )
        ],
        responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})}
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass
        logout(request)
        return Response({"message": "Logged out successfully"})


@extend_schema(
    tags=["Account - Profile"],
    request=None,
    examples=[
        OpenApiExample(
            "Close Account",
            value={},
            request_only=True
        )
    ],
    responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})}
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def close_account(request):
    user = request.user

    try:
        virtual_account = VirtualAccount.objects.filter(user=user).first()
        if virtual_account:
            client = PaystackGateway(settings.PAYSTACK_SECRET_KEY)
            client.close_virtual_account(virtual_account.account_reference)
            virtual_account.status = "CLOSED"
            virtual_account.save()

        user.is_active = False
        user.save()

        return Response({"message": "Account closed successfully"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=["Account - Profile"],
    request=None,
    examples=[
        OpenApiExample(
            "Generate Virtual Account",
            value={},
            request_only=True
        )
    ],
    responses={200: inline_serializer("GenerateVirtualAccountResponse", fields={"success": serializers.BooleanField(), "message": serializers.CharField()})}
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def generate_virtual_account(request):
    user = request.user

    if hasattr(user, 'virtual_account'):
        return Response({"success": False, "error": "User already has a virtual account"}, status=400)

    if not user.first_name or not user.last_name or not user.email:
        return Response({"success": False, "error": "User profile information is incomplete. First name, last name, and email are required."}, status=400)

    try:
        client = PaystackGateway(settings.PAYSTACK_SECRET_KEY)

        account_res = client.create_virtual_account(
            user.email,
            user.first_name,
            user.middle_name or "",
            user.last_name,
            user.phone_country_code + user.phone_number,
        )

        if account_res is not None:
            return Response({"success": account_res['status'], "message": account_res['message']}, status=200)
        else:
            return Response({"success": False, "error": "Virtual account generation failed due to an unexpected error"}, status=500)

    except Exception as e:
        print(e)
        return Response({"success": False, "error": str(e)}, status=500)
