from rest_framework import viewsets, views, generics
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
import pyotp
from admin_api.models import AdminBeneficiary, AdminTransferLog
from admin_api.serializers import AdminBeneficiarySerializer, AdminTransferLogSerializer
from admin_api.permissions import CanInitiateTransfers

@extend_schema(tags=["Admin Administrative Transfers"])
class AdminBeneficiaryViewSet(viewsets.ModelViewSet):
    serializer_class = AdminBeneficiarySerializer
    permission_classes = [CanInitiateTransfers]
    queryset = AdminBeneficiary.objects.all()

@extend_schema(tags=["Admin Administrative Transfers"])
class AdminInitiateTransferView(views.APIView):
    permission_classes = [CanInitiateTransfers]

    def post(self, request):
        beneficiary_id = request.data.get('beneficiary_id')
        amount = float(request.data.get('amount', 0))
        otp = request.data.get('otp')
        
        user = request.user
        if user.two_factor_secret:
            totp = pyotp.TOTP(user.two_factor_secret)
            if not otp or not totp.verify(otp):
                return Response({"error": "Invalid or missing OTP"}, status=403)

        return Response({"status": "Transfer initiated (Placeholder for production gateway call)"})

@extend_schema(tags=["Admin Administrative Transfers"])
class AdminTransferLogView(generics.ListAPIView):
    serializer_class = AdminTransferLogSerializer
    permission_classes = [CanInitiateTransfers]
    queryset = AdminTransferLog.objects.all().order_by('-created_at')
