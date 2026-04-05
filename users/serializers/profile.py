from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import OTP, KYC

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField()
    all_permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "phone_country_code", "phone_number", "first_name", "last_name", "middle_name",
            "email", "is_verified", "email_verified", "phone_number_verified", "is_active",
            "role", "referral_code", "profile_image",
            "transaction_pin_set", "created_at",
            "groups", "all_permissions",
        ]
        read_only_fields = fields

    def get_groups(self, obj):
        return list(obj.groups.values('id', 'name'))

    def get_all_permissions(self, obj):
        if obj.is_staff or obj.is_superuser:
            return sorted(list(obj.get_all_permissions()))
        return []

class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "middle_name", "profile_image"]

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
        if not OTP.objects.filter(user=user, code=attrs['otp_code'], purpose='reset', is_used=False).exists():
            raise serializers.ValidationError("Invalid or expired OTP.")
        return attrs

class VerifyTransactionPinSerializer(serializers.Serializer):
    pin = serializers.CharField(min_length=4, max_length=4)

class KYCSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYC
        fields = ['id_type', 'id_number', 'id_image', 'face_image']

    def validate(self, attrs):
        user = self.context['request'].user
        if hasattr(user, 'kyc') and user.kyc.status == 'APPROVED':
            raise serializers.ValidationError("KYC already approved.")
        return attrs

class KYCStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYC
        fields = ['status', 'remarks', 'created_at', 'updated_at', 'id_type', 'id_number']
