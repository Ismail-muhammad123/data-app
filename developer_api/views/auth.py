from rest_framework import status, generics, permissions, serializers
from rest_framework.response import Response
from django.db import transaction
from django.contrib.auth import get_user_model
from wallet.utils import fund_wallet
from summary.models import SiteConfig
from ..models import DeveloperProfile, APIKey

User = get_user_model()

class DeveloperProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeveloperProfile
        fields = ['webhook_url', 'webhook_secret', 'created_at']

class APIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = APIKey
        fields = ['key', 'mode', 'is_active', 'created_at', 'last_used']

class UpgradeToDeveloperView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        if hasattr(user, 'developer_profile'):
            return Response({"error": "You are already a developer."}, status=status.HTTP_400_BAD_REQUEST)

        config = SiteConfig.objects.first()
        fee = config.developer_upgrade_fee if config else 0

        if user.wallet.balance < fee:
            return Response({"error": f"Insufficient balance. Upgrade fee is {fee}."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                if fee > 0:
                    fund_wallet(
                        user_id=user.id,
                        amount=-float(fee),
                        description="Developer API Upgrade Fee",
                        initiator="system"
                    )
                
                profile = DeveloperProfile.objects.create(user=user)
                APIKey.objects.create(profile=profile, key=APIKey.generate_key(mode='live'), mode='live')
                APIKey.objects.create(profile=profile, key=APIKey.generate_key(mode='sandbox'), mode='sandbox')
                
            return Response({
                "message": "Successfully upgraded to developer.",
                "fee_deducted": float(fee)
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeveloperDetailsView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeveloperProfileSerializer

    def get_object(self):
        try: return self.request.user.developer_profile
        except DeveloperProfile.DoesNotExist: return None

    def retrieve(self, request, *args, **kwargs):
        profile = self.get_object()
        if not profile:
            return Response({"error": "Not a developer"}, status=403)
        
        keys = APIKey.objects.filter(profile=profile)
        return Response({
            "profile": self.get_serializer(profile).data,
            "api_keys": APIKeySerializer(keys, many=True).data
        })

class RegenerateAPIKeyView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        mode = request.data.get('mode', 'live')
        try:
            profile = request.user.developer_profile
            APIKey.objects.filter(profile=profile, mode=mode).update(is_active=False)
            new_key = APIKey.objects.create(
                profile=profile, 
                key=APIKey.generate_key(mode=mode), 
                mode=mode
            )
            return Response(APIKeySerializer(new_key).data)
        except DeveloperProfile.DoesNotExist:
            return Response({"error": "Not a developer"}, status=403)
