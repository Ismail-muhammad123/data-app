from rest_framework import viewsets, views, generics
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample
import pyotp
from admin_api.models import AdminBeneficiary, AdminTransferLog
from admin_api.serializers import AdminBeneficiarySerializer, AdminTransferLogSerializer, AdminInitiateTransferRequestSerializer
from admin_api.permissions import CanInitiateTransfers

@extend_schema(tags=["Admin Administrative Transfers"])
class AdminBeneficiaryViewSet(viewsets.ModelViewSet):
    serializer_class = AdminBeneficiarySerializer
    permission_classes = [CanInitiateTransfers]
    queryset = AdminBeneficiary.objects.all()

@extend_schema(
    tags=["Admin Administrative Transfers"],
    summary="Initiate admin transfer",
    description="Initiate an administrative bank transfer. Requires a valid beneficiary ID, amount, and admin OTP.",
    request=AdminInitiateTransferRequestSerializer,
    responses={200: {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}}, 403: {"type": "object", "properties": {"error": {"type": "string"}}}},
    examples=[
        OpenApiExample(
            'Initiate Admin Transfer Request',
            description='Example of a request to initiate an admin-level bank transfer.',
            value={
                "beneficiary_id": 12,
                "amount": 10000.00,
                "otp": "654321"
            },
            request_only=True
        )
    ]
)
class AdminInitiateTransferView(views.APIView):
    permission_classes = [CanInitiateTransfers]

    def post(self, request):
        serializer = AdminInitiateTransferRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        beneficiary_id = serializer.validated_data['beneficiary_id']
        amount = float(serializer.validated_data['amount'])
        otp = serializer.validated_data.get('otp')
        
        user = request.user
        if user.two_factor_secret:
            totp = pyotp.TOTP(user.two_factor_secret)
            if not otp or not totp.verify(otp):
                return Response({"error": "Invalid or missing OTP"}, status=403)

        # Logic to record the transfer and trigger the gateway
        return Response({
            "status": "SUCCESS", 
            "message": "Transfer initiated (Placeholder for production gateway call)"
        })

@extend_schema(tags=["Admin Administrative Transfers"])
class AdminTransferLogView(generics.ListAPIView):
    serializer_class = AdminTransferLogSerializer
    permission_classes = [CanInitiateTransfers]
    queryset = AdminTransferLog.objects.all().order_by('-created_at')
