from django.contrib.auth import get_user_model, logout, authenticate
from rest_framework import status, generics, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample, inline_serializer
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from users.models import OTP, Referral
from users.utils import send_otp_code
from users.serializers import (
    LoginSerializer, SignupSerializer, GoogleAuthSerializer, 
    Verify2FASerializer, ProfileSerializer
)

User = get_user_model()

class LoginView(APIView):
    @extend_schema(
        tags=["Account - Auth"],
        request=LoginSerializer,
        responses={200: inline_serializer(name="LoginResponse", fields={"refresh": serializers.CharField(), "access": serializers.CharField(), "user": ProfileSerializer()})}
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
            return Response({"error": "Account not active"}, status=status.HTTP_403_FORBIDDEN)
        
        from summary.models import SiteConfig
        config = SiteConfig.objects.first()
        is_staff_enforced = user.is_staff and config and config.enforce_2fa_for_staff
        if is_staff_enforced or user.is_2fa_enabled:
            send_otp_code(user, "2fa")
            return Response({"two_factor_required": True, "message": "A 2FA code has been sent.", "identifier": user.phone_number}, status=status.HTTP_200_OK)
        
        refresh = RefreshToken.for_user(user)
        return Response({"refresh": str(refresh), "access": str(refresh.access_token), "user": ProfileSerializer(user).data})

class RefreshTokenView(APIView):
    permission_classes = [permissions.AllowAny]
    @extend_schema(tags=["Account - Auth"], request=inline_serializer("RefreshTokenRequest", fields={"refresh": serializers.CharField()}), responses={200: inline_serializer("RefreshTokenResponse", fields={"access": serializers.CharField()})})
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            refresh = RefreshToken(refresh_token)
            return Response({"access": str(refresh.access_token)}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)

class GoogleAuthView(APIView):
    permission_classes = [permissions.AllowAny]
    @extend_schema(tags=["Account - Auth"], request=GoogleAuthSerializer, responses={200: inline_serializer("GoogleAuthResponse", fields={"refresh": serializers.CharField(), "access": serializers.CharField(), "user": ProfileSerializer()})})
    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["id_token"]
        phone_number = serializer.validated_data.get("phone_number")
        referral_code = serializer.validated_data.get("referral_code")
        try:
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
            email, google_id = idinfo['email'], idinfo['sub']
            user = User.objects.filter(google_id=google_id).first() or User.objects.filter(email=email).first()
            if not user:
                if not phone_number:
                    return Response({"error": "Phone number required", "code": "PHONE_NUMBER_REQUIRED", "google_data": idinfo}, status=status.HTTP_400_BAD_REQUEST)
                user = User.objects.create_user(phone_number=phone_number, email=email, google_id=google_id, is_active=True, email_verified=True, is_verified=True)
                if referral_code:
                    try:
                        referrer = User.objects.get(referral_code=referral_code)
                        Referral.objects.create(referrer=referrer, referred=user)
                    except User.DoesNotExist: pass
            elif not user.google_id:
                user.google_id = google_id
                user.save(update_fields=['google_id'])
            refresh = RefreshToken.for_user(user)
            return Response({"refresh": str(refresh), "access": str(refresh.access_token), "user": ProfileSerializer(user).data})
        except ValueError:
            return Response({"error": "Invalid Google token"}, status=status.HTTP_400_BAD_REQUEST)

class Verify2FAView(APIView):
    permission_classes = [permissions.AllowAny]
    @extend_schema(tags=["Account - 2FA"], request=Verify2FASerializer, responses={200: inline_serializer("Verify2FAResponse", fields={"refresh": serializers.CharField(), "access": serializers.CharField(), "user": ProfileSerializer()})})
    def post(self, request):
        serializer = Verify2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(email=serializer.validated_data["identifier"]) if "@" in serializer.validated_data["identifier"] else User.objects.get(phone_number=serializer.validated_data["identifier"])
        otp = OTP.objects.get(user=user, code=serializer.validated_data["otp_code"], purpose="2fa", is_used=False)
        otp.is_used = True
        otp.save()
        refresh = RefreshToken.for_user(user)
        return Response({"refresh": str(refresh), "access": str(refresh.access_token), "user": ProfileSerializer(user).data})

@extend_schema(tags=["Account - Auth"])
class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignupSerializer
    
    @extend_schema(tags=["Account - Auth"], request=SignupSerializer, responses={201: SignupSerializer})
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class ResendActivationCodeView(APIView):
    @extend_schema(tags=["Account - Auth"], responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})})
    def post(self, request):
        identifier, channel = request.data.get("identifier"), request.data.get("channel")
        user = User.objects.get(phone_number=identifier)
        if user.is_verified: return Response({"error": "Already verified"}, status=400)
        send_otp_code(user, "activation", preferred_channel=channel)
        return Response({"message": "Code resent"})

class ActivateAccountView(APIView):
    @extend_schema(tags=["Account - Auth"], responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})})
    def post(self, request):
        user = User.objects.get(phone_number=request.data.get("identifier"))
        otp = OTP.objects.get(user=user, code=request.data.get("otp"), purpose="activation", is_used=False)
        user.is_active = user.is_verified = True
        if otp.channel == "email": user.email_verified = True
        elif otp.channel in ["sms", "whatsapp"]: user.phone_number_verified = True
        user.save()
        otp.is_used = True
        otp.save()
        from summary.models import SiteConfig
        from wallet.utils import fund_wallet, process_referral_reward
        config = SiteConfig.objects.first()
        if config and config.signup_bonus_enabled:
            fund_wallet(user.id, float(config.signup_bonus_amount), description="Signup Bonus")
        process_referral_reward(user, trigger_event='signup')
        return Response({"message": "Activated"})

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Account - Auth"], responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})})
    def post(self, request):
        try: RefreshToken(request.data.get("refresh")).blacklist()
        except: pass
        logout(request)
        return Response({"message": "Logged out"})
