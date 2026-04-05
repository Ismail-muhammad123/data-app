from rest_framework import status, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from drf_spectacular.utils import extend_schema, OpenApiExample, inline_serializer
from django.conf import settings
from users.models import User, OTP
from users.utils import send_otp_code
from users.serializers import (
    ProfileSerializer, UpdateProfileSerializer, ChangePINSerializer, 
    PasswordResetSerializer, SetTransactionPinSerializer, 
    ChangeTransactionPinSerializer, ResetTransactionPinSerializer, 
    VerifyTransactionPinSerializer
)

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Account - Profile"], responses={200: ProfileSerializer})
    def get(self, request): return Response(ProfileSerializer(request.user).data)
    @extend_schema(tags=["Account - Profile"], request=UpdateProfileSerializer, responses={200: UpdateProfileSerializer})
    def post(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class Update2FASettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Account - 2FA"], request=inline_serializer("Update2FAStatusRequest", fields={"is_2fa_enabled": serializers.BooleanField(), "two_factor_method": serializers.ChoiceField(choices=User.TWO_FACTOR_METHODS)}), responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})})
    def post(self, request):
        request.user.is_2fa_enabled = request.data.get("is_2fa_enabled", request.user.is_2fa_enabled)
        request.user.two_factor_method = request.data.get("two_factor_method", request.user.two_factor_method)
        request.user.save()
        return Response({"message": "2FA settings updated"})

class ChangePINView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Account - Profile"], request=ChangePINSerializer, responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})})
    def post(self, request):
        serializer = ChangePINSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "PIN changed"})

class PasswordResetRequestView(APIView):
    @extend_schema(tags=["Account - Auth"], request=inline_serializer("PasswordResetRequest", fields={"identifier": serializers.CharField()}), responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})})
    def post(self, request):
        user = User.objects.get(phone_number=request.data.get("identifier"))
        send_otp_code(user, "reset")
        return Response({"message": "OTP sent"})

class PasswordResetConfirmView(APIView):
    @extend_schema(tags=["Account - Auth"], request=PasswordResetSerializer, responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})})
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "PIN reset successful"})

class SetTransactionPinView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Account - Transaction PIN"], request=SetTransactionPinSerializer, responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})})
    def post(self, request):
        serializer = SetTransactionPinSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_transaction_pin(serializer.validated_data['pin'])
        return Response({"message": "Transaction PIN set"})

class ChangeTransactionPinView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Account - Transaction PIN"], request=ChangeTransactionPinSerializer, responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})})
    def post(self, request):
        serializer = ChangeTransactionPinSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_transaction_pin(serializer.validated_data['new_pin'])
        return Response({"message": "Transaction PIN changed"})

class ResetTransactionPinView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Account - Transaction PIN"], request=ResetTransactionPinSerializer, responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})})
    def post(self, request):
        serializer = ResetTransactionPinSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        OTP.objects.filter(user=request.user, code=serializer.validated_data['otp_code'], purpose='reset', is_used=False).update(is_used=True)
        request.user.set_transaction_pin(serializer.validated_data['new_pin'])
        return Response({"message": "Transaction PIN reset"})

class RequestTransactionPinResetOTPView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Account - Transaction PIN"], responses={200: inline_serializer("MessageResponse", fields={"message": serializers.CharField()})})
    def post(self, request):
        send_otp_code(request.user, "reset")
        return Response({"message": "OTP sent"})

class VerifyTransactionPinView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(tags=["Account - Transaction PIN"], request=VerifyTransactionPinSerializer, responses={200: inline_serializer("VerifyPinResponse", fields={"valid": serializers.BooleanField()})})
    def post(self, request):
        is_valid = request.user.check_transaction_pin(request.data.get('pin'))
        return Response({"valid": is_valid})

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def close_account(request):
    from wallet.models import VirtualAccount
    from payments.utils import PaystackGateway
    user = request.user
    va = VirtualAccount.objects.filter(user=user).first()
    if va:
        PaystackGateway(settings.PAYSTACK_SECRET_KEY).close_virtual_account(va.account_reference)
        va.status = "CLOSED"; va.save()
    user.is_active = False; user.save()
    return Response({"message": "Account closed"})

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def generate_virtual_account(request):
    from payments.utils import PaystackGateway
    user = request.user
    if hasattr(user, 'virtual_account'):
        return Response({"success": False, "error": "User already has a virtual account"}, status=400)
    if not user.first_name or not user.last_name or not user.email:
        return Response({"success": False, "error": "First name, last name, and email are required."}, status=400)
    try:
        res = PaystackGateway(settings.PAYSTACK_SECRET_KEY).create_virtual_account(user.email, user.first_name, user.middle_name or "", user.last_name, user.phone_country_code + user.phone_number)
        if res: return Response({"success": res['status'], "message": res['message']})
        return Response({"success": False, "error": "Fail"}, status=500)
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)
