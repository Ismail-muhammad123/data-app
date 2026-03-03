# users/views.py
from django.contrib.auth import get_user_model, logout
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import OTP
from .serializers import (
    ChangePINSerializer,
    LoginSerializer,
    PasswordResetSerializer,
    ProfileSerializer,
    SignupSerializer,
    UpdateProfileSerializer
)
from .utils import send_otp_code
from django.contrib.auth import authenticate
from django.conf import settings

from rest_framework.decorators import api_view, permission_classes
from wallet.models import VirtualAccount
from wallet.serializers import VirtualAccountSerializer
from payments.utils import PaystackGateway


User = get_user_model()

# --------------------
# Login (Phone + PIN)
# --------------------
class LoginView(APIView):
    """Login with phone number and PIN"""

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone_number"]
        pin = serializer.validated_data["pin"]

        user = authenticate(username=phone, password=pin)
        if not user:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({"error": "Account not active"}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": ProfileSerializer(user).data
        })

class RefreshTokenView(APIView):
    """
    Obtain a new access token using a refresh token.
    """
    permission_classes = [permissions.AllowAny]

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
# ---------------------------
# Signup (Phone + PIN auth)
# ---------------------------
class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignupSerializer

    def perform_create(self, serializer):
        user = serializer.save(is_active=True)  # wait for OTP verification
        # send_otp_code(user, "activation")  # se   nd OTP to email/phone/whatsapp

class ResendActivationCodeView(APIView):
    def post(self, request):
        identifier = request.data.get("identifier")  # phone/email
        channel = request.data.get("channel", None)  # default to phone if not specified

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
    def post(self, request):
        identifier = request.data.get("identifier")  # phone/email
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

        return Response({"message": "Account activated successfully."}, status=status.HTTP_200_OK)


# ----------------------
# Profile
# ----------------------
class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # TODO add wallet info, and purchase info
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        if request.user.email and request.data.get("email") and request.user.email != request.data.get("email"):
            users = User.objects.filter(email=request.data.get("email"), email_verified=True).exclude(id=request.user.id)
            if users.exists():
                return Response({"error": "Email already in use."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# --------------------------
# Password Reset (via OTP)
# --------------------------
class PasswordResetRequestView(APIView):
    def post(self, request):
        identifier = request.data.get("identifier")  # phone/email
        identifier = identifier[1:] if identifier and identifier.startswith("0") else identifier  # Remove leading zero if present

        try:
            user = User.objects.get(phone_number=identifier)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        send_otp_code(user, "reset")
        return Response({"message": "OTP sent for password reset"})


class PasswordResetConfirmView(APIView):
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "PIN reset successful"})


# ----------------------
# Change PIN
# ----------------------
class ChangePINView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePINSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "PIN changed successfully"})


# ----------------------
# Logout
# ----------------------
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass
        logout(request)
        return Response({"message": "Logged out successfully"})


# ----------------------
# Close Account
# ----------------------
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def close_account(request):
    user = request.user
    
    try:
        # Close virtual account if it exists
        virtual_account = VirtualAccount.objects.filter(user=user).first()
        if virtual_account:
            client = PaystackGateway(settings.PAYSTACK_SECRET_KEY)
            client.close_virtual_account(virtual_account.account_reference)
            virtual_account.status = "CLOSED"
            virtual_account.save()
        
        # Deactivate user account
        user.is_active = False
        user.save()
        
        return Response({"message": "Account closed successfully"}, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ----------------------------------
# Upgrade account tier
# ----------------------------------
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def generate_virtual_account(request):
    user = request.user

    # Check if a virtual account already exists
    if hasattr(user, 'virtual_account'):
        return Response({"success": False, "error": "User already has a virtual account"}, status=400)

    # Check if profile is complete enough for Paystack (Email and Names are required)
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
    

