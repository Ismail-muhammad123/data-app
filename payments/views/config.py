from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from summary.models import SiteConfig

class ChargesConfigView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        config = SiteConfig.objects.first()
        return Response({
            "withdrawal_charge": float(config.withdrawal_charge) if config else 0.0,
            "deposit_charge": float(config.crediting_charge) if config else 0.0,
        }, status=status.HTTP_200_OK)
