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
from rest_framework.decorators import action
from rest_framework import viewsets

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

# ---------------------------
# Signup (Phone + PIN auth)
# ---------------------------
class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignupSerializer

    def perform_create(self, serializer):
        user = serializer.save(is_active=False)  # wait for OTP verification
        send_otp_code(user, "activation")  # send OTP to email/phone/whatsapp

class ResendActivationCodeView(APIView):
    def post(self, request):
        identifier = request.data.get("identifier")  # phone/email

        if not identifier:
            return Response({"error": "Phone Number is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(phone_number=identifier)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_active:
            return Response({"error": "Account is already active."}, status=status.HTTP_400_BAD_REQUEST)

        send_otp_code(user, "activation")
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
            otp = OTP.objects.get(user=user, code=otp_code, purpose="signup", is_used=False)
        except OTP.DoesNotExist:
            return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save()
        otp.is_used = True
        otp.save()

        return Response({"message": "Account activated successfully."}, status=status.HTTP_200_OK)


# ----------------------
# Profilex
# ----------------------
class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ----------------------
# Password Reset (via OTP)
# ----------------------
class PasswordResetRequestView(APIView):
    def post(self, request):
        identifier = request.data.get("identifier")  # phone/email
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




# ----------------------------------
# Admin Views
# ----------------------------------

class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_staff=True)
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return User.objects.filter(is_staff=True)

    def perform_create(self, serializer):
        serializer.save(is_staff=True, is_superuser=False, is_active=True)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def set_password(self, request, pk=None):
        user = self.get_object()
        password = request.data.get("password")
        if not password:
            return Response({"error": "Password required"}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(password)
        user.save()
        return Response({"message": "Password updated successfully"})