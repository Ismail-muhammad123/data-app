from rest_framework import serializers
from .models import User, OTP
from .utils import generate_otp, otp_expiry
from django.contrib.auth import get_user_model

User = get_user_model()




class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    pin = serializers.CharField()


class SignupSerializer(serializers.ModelSerializer):
    pin = serializers.CharField(write_only=True, min_length=4, max_length=6)

    class Meta:
        model = User
        fields = ["phone_country_code", "phone_number", "email", "pin"]

    def create(self, validated_data):
        pin = validated_data.pop("pin")
        user = User.objects.create_user(**validated_data, password=pin)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","phone_country_code", "full_name", "phone_number", "email", "is_active", "created_at"]


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "full_name"] 



class PasswordResetSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    otp_code = serializers.CharField()
    new_pin = serializers.CharField(min_length=4, max_length=6)

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        otp_code = attrs.get("otp_code")

        try:
            user = User.objects.get(phone_number=identifier)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        from .models import OTP
        if not OTP.objects.filter(user=user, code=otp_code, is_used=False).exists():
            raise serializers.ValidationError("Invalid or expired OTP")

        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_pin"])
        user.save()
        OTP.objects.filter(user=user, code=self.validated_data["otp_code"]).update(is_used=True)
        return user


class ChangePINSerializer(serializers.Serializer):
    old_pin = serializers.CharField()
    new_pin = serializers.CharField(min_length=4, max_length=6)

    def validate(self, attrs):
        user = self.context["user"]
        if not user.check_password(attrs.get("old_pin")):
            raise serializers.ValidationError("Old PIN is incorrect")
        return attrs

    def save(self, **kwargs):
        user = self.context["user"]
        user.set_password(self.validated_data["new_pin"])
        user.save()
        return user


# class OTPRequestSerializer(serializers.Serializer):
#     phone_number = serializers.CharField()
#     purpose = serializers.ChoiceField(choices=OTP.PURPOSE_CHOICES)
