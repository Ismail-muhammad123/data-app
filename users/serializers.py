from rest_framework import serializers
from .models import User, OTP, Referral, ReferralConfig
from django.contrib.auth import get_user_model

User = get_user_model()


# ─── Auth Serializers ───

class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    pin = serializers.CharField()


class SignupSerializer(serializers.ModelSerializer):
    pin = serializers.CharField(write_only=True, min_length=4, max_length=6)
    referral_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "phone_country_code", "phone_number", "email", "pin",
            "first_name", "last_name", "middle_name",
            "referral_code",
        ]
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
            "middle_name": {"required": False},
            "email": {"required": False},
        }

    def validate_referral_code(self, value):
        if value:
            if not User.objects.filter(referral_code=value).exists():
                raise serializers.ValidationError("Invalid referral code.")
        return value

    def create(self, validated_data):
        pin = validated_data.pop("pin")
        referral_code_input = validated_data.pop("referral_code", None)

        user = User.objects.create_user(**validated_data, password=pin)
        # ============ TODO: remove the following two lines after testing =============
        user.is_active = True
        user.save()
        # =============================================================================

        # Create referral link if a valid code was provided
        if referral_code_input:
            try:
                referrer = User.objects.get(referral_code=referral_code_input)
                referral = Referral.objects.create(referrer=referrer, referred=user)

                # Pay signup bonus if referral program is active and mode is 'signup'
                config = ReferralConfig.objects.first()
                if config and config.is_active and config.commission_mode == 'signup':
                    from wallet.utils import fund_wallet
                    from django.db.models import F
                    bonus = config.commission_value
                    
                    # 1. Credit wallet
                    fund_wallet(
                        referrer.id,
                        float(bonus),
                        description=f"Referral bonus: {user.phone_number} signed up with your code",
                    )
                    
                    # 2. Update referral record
                    referral.bonus_paid = True
                    referral.bonus_amount = bonus
                    referral.save()

                    # 3. Update referrer metrics
                    referrer.referral_earnings_count = F('referral_earnings_count') + 1
                    referrer.referral_earnings_amount = F('referral_earnings_amount') + bonus
                    referrer.save(update_fields=['referral_earnings_count', 'referral_earnings_amount'])
            except User.DoesNotExist:
                pass  # Silently ignore if referrer not found

        return user


# ─── Profile Serializers ───

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "phone_country_code",
            "phone_number",
            "first_name", "last_name", "middle_name",
            "email",
            "is_verified",
            "email_verified",
            "phone_number_verified",
            "is_active",
            "role",
            "referral_code",
            "profile_picture_url",
            "transaction_pin_set",
            "created_at",
        ]
        read_only_fields = fields


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "middle_name", "profile_picture_url"]


# ─── PIN Management Serializers ───

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


# ─── Transaction PIN Serializers ───

class SetTransactionPinSerializer(serializers.Serializer):
    pin = serializers.CharField(min_length=4, max_length=4)
    confirm_pin = serializers.CharField(min_length=4, max_length=4)

    def validate(self, attrs):
        if attrs['pin'] != attrs['confirm_pin']:
            raise serializers.ValidationError("PINs do not match.")
        user = self.context['request'].user
        if user.transaction_pin_set:
            raise serializers.ValidationError("Transaction PIN already set. Use the change PIN endpoint.")
        return attrs


class ChangeTransactionPinSerializer(serializers.Serializer):
    old_pin = serializers.CharField(min_length=4, max_length=4)
    new_pin = serializers.CharField(min_length=4, max_length=4)
    confirm_pin = serializers.CharField(min_length=4, max_length=4)

    def validate(self, attrs):
        if attrs['new_pin'] != attrs['confirm_pin']:
            raise serializers.ValidationError("New PINs do not match.")
        user = self.context['request'].user
        if not user.check_transaction_pin(attrs['old_pin']):
            raise serializers.ValidationError("Current transaction PIN is incorrect.")
        return attrs


class ResetTransactionPinSerializer(serializers.Serializer):
    otp_code = serializers.CharField()
    new_pin = serializers.CharField(min_length=4, max_length=4)
    confirm_pin = serializers.CharField(min_length=4, max_length=4)

    def validate(self, attrs):
        if attrs['new_pin'] != attrs['confirm_pin']:
            raise serializers.ValidationError("PINs do not match.")
        user = self.context['request'].user
        from .models import OTP as OTPModel
        if not OTPModel.objects.filter(user=user, code=attrs['otp_code'], purpose='reset', is_used=False).exists():
            raise serializers.ValidationError("Invalid or expired OTP.")
        return attrs


# ─── Referral Serializers ───

class ReferralSerializer(serializers.ModelSerializer):
    referred_phone = serializers.CharField(source='referred.phone_number', read_only=True)
    referred_name = serializers.CharField(source='referred.full_name', read_only=True)

    class Meta:
        model = Referral
        fields = ['id', 'referred_phone', 'referred_name', 'bonus_paid', 'bonus_amount', 'created_at']
        read_only_fields = fields


class VerifyTransactionPinSerializer(serializers.Serializer):
    pin = serializers.CharField(min_length=4, max_length=4)

# ─── FCM Token Serializer ───

class FCMTokenSerializer(serializers.Serializer):
    token = serializers.CharField()
