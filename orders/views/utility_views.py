import logging
import random
import string
from datetime import datetime
import pytz
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema
from orders.router import ProviderRouter
from orders.serializers import (
    VerifyCustomerRequestSerializer, VerifyCustomerResponseSerializer,
    ErrorResponseSerializer
)

logger = logging.getLogger(__name__)

def generate_request_id():
    lagos_tz = pytz.timezone("Africa/Lagos")
    now = datetime.now(lagos_tz)
    numeric_part = now.strftime("%Y%m%d%H%M")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{numeric_part}-{random_part}"

class VerifyCustomerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Orders - Verification"],
        summary="Verify a customer (TV, Electricity, Internet)",
        description="Validate a customer's smart card number, meter number, or Internet sub account before purchase.",
        request=VerifyCustomerRequestSerializer,
        responses={
            200: VerifyCustomerResponseSerializer,
            400: ErrorResponseSerializer,
        }
    )
    def post(self, request):
        serializer = VerifyCustomerRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service_id = serializer.validated_data["service_id"]
        customer_id = serializer.validated_data["customer_id"]
        purchase_type = serializer.validated_data.get("purchase_type", "tv")

        try:
            if purchase_type == 'tv':
                action = 'validate_cable_id'
                kwargs = {'card_number': customer_id, 'service': service_id}
            elif purchase_type == 'electricity':
                action = 'validate_meter'
                kwargs = {'meter_number': customer_id, 'service': service_id}
            elif purchase_type == 'internet':
                action = 'verify_internet'
                kwargs = {'accountID': customer_id}
            else:
                action = 'validate_cable_id'
                kwargs = {'card_number': customer_id, 'service': service_id}
            
            res = ProviderRouter.execute_with_fallback(purchase_type, action, **kwargs)
            print(f"Beneficiary Verification result: {res}")

            response_status = status.HTTP_200_OK if res.get("status") in ["SUCCESS", "ORDER_RECEIVED"] else status.HTTP_400_BAD_REQUEST

            return Response(res, status=response_status)

        except Exception as e:
            logger.error(f"Customer verification failed: {str(e)}")
            return Response({"error": "Verification failed."}, status=status.HTTP_400_BAD_REQUEST)
