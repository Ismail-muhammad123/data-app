import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics

from orders.models import DataService, DataVariation, ElectricityService, Purchase, AirtimeNetwork, TVService, TVVariation
# from orders.utils import buy_airtime, buy_data_plan
from orders.services.clubkonnect import ClubKonnectClient
from wallet.models import Wallet
from wallet.utils import debit_wallet, fund_wallet
from .serializers import (
    AirtimePurchaseRequestSerializer, 
    DataServiceSerializer, 
    DataVariationSerializer, 
    DataPurchaseRequestSerializer,
    ElectricityPurchaseRequestSerializer, 
    PurchaseSerializer, 
    AirtimeNetworkSerializer,
    TVPurchaseRequestSerializer,
    TVServiceSerializer,
    TVVariationSerializer
)

import logging

logger = logging.getLogger(__name__)


from datetime import datetime
import pytz
import random
import string

def generate_request_id():
    # Set timezone to Africa/Lagos (GMT+1)
    lagos_tz = pytz.timezone("Africa/Lagos")
    now = datetime.now(lagos_tz)
    
    # Generate first 12 numeric characters from date and time
    # Format: YYYYMMDDHHMM (YearMonthDayHourMinute)
    numeric_part = now.strftime("%Y%m%d%H%M")
    
    # Optionally add 3–5 random alphanumeric characters for uniqueness
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    # Combine them
    request_id = f"{numeric_part}-{random_part}"
    
    return request_id



# ---------- CUSTOMER ----------
class DataServicesListView(generics.ListAPIView):
    queryset = DataService.objects.all()
    serializer_class = DataServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

class DataVariationsListView(generics.ListAPIView):
    queryset = DataVariation.objects.all()
    serializer_class = DataVariationSerializer
    permission_classes = [permissions.IsAuthenticated]


    def get_queryset(self):
        queryset = DataVariation.objects.filter(is_active=True)
        service_id = self.request.query_params.get("service_id")
        if service_id:
            queryset = queryset.filter(service__id=service_id)

        return queryset

class AirtimeNetworkListView(generics.ListAPIView):
    queryset = AirtimeNetwork.objects.all()
    serializer_class = AirtimeNetworkSerializer
    permission_classes = [permissions.IsAuthenticated]

class PurchaseDataVariationView(APIView):
    permission_classes=  [permissions.IsAuthenticated]
    serializer_class = DataPurchaseRequestSerializer

    def post(self, request):
        serializer = DataPurchaseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan_id = serializer.validated_data["plan_id"]
        phone_number = serializer.validated_data["phone_number"]

        try:
            plan = DataVariation.objects.get(id=plan_id, is_active=True)
        except DataVariation.DoesNotExist:
            return Response({"error": "Invalid or inactive plan."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        amount = plan.selling_price

        wallet, _ = Wallet.objects.get_or_create(user=user)

        if wallet.balance < amount:
            return Response({"error": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)

        
        reference = generate_request_id()
        # # Step 3: Call VTPass
        # vtpass_response = buy_data_plan(
        #     service_id=plan.service_type.service_id,
        #     phone_number=phone_number,
        #     amount=amount,
        #     request_id=reference,
        #     variation_code=plan.variation_code,
        # )


        client = ClubKonnectClient()

        try:
            resp = client.buy_data(
                request_id=reference, 
                phone=phone_number, 
                network_id=plan.service.service_id, 
                plan_id=plan.variation_id
            )

            if resp.get("status") == "success":
                # Step 1: Debit wallet
                debit_wallet(user.id, amount, f"{plan.service.service_name} purchase - {reference}")

                # Step 2: Create transaction record
                transaction = Purchase.objects.create(
                    user=user,
                    purchase_type="data",
                    data_variation=plan,
                    beneficiary=phone_number,
                    reference=reference,
                    amount=amount,
                    status="success"
                )
                return Response(PurchaseSerializer(transaction).data, status=status.HTTP_201_CREATED)
            else:
                return Response({"error": resp.get("message", "Transaction failed")}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Data purchase failed: {str(e)}")
            return Response({"error": "Transaction failed"}, status=status.HTTP_400_BAD_REQUEST)

class PurchaseAirtimeView(APIView):
    permission_classes=  [permissions.IsAuthenticated]
    serializer_class = DataPurchaseRequestSerializer

    def post(self, request):
        serializer = AirtimePurchaseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]
        phone_number = serializer.validated_data["phone_number"]
        service_id = serializer.validated_data["service_id"]

        try:
            network = AirtimeNetwork.objects.get(service_id=service_id)
        except AirtimeNetwork.DoesNotExist:
            return Response({"error": "Invalid Service."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        wallet, _ = Wallet.objects.get_or_create(user=user)

        if wallet.balance < amount:
            return Response({"error": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)


        reference = generate_request_id()

        client = ClubKonnectClient()

        try:
            resp = client.buy_airtime(
                request_id=reference, 
                phone=phone_number, 
                network_id=network.service_id, 
                amount=amount,
            )

            if resp.get("status") == "success":
                # Step 1: Debit wallet
                debit_wallet(user.id, amount, f"{network.service_name} Airtime purchase - {reference}")
                
                # Step 2: Create transaction record
                transaction = Purchase.objects.create(
                    user=user,
                    purchase_type="airtime",
                    airtime_service=network,
                    beneficiary=phone_number,
                    reference=reference,
                    amount=amount,
                    status="success"
                )
                return Response(PurchaseSerializer(transaction).data, status=status.HTTP_201_CREATED)

            else:
                return Response({"error": resp.get("message", "Transaction failed")}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Airtime purchase failed: {str(e)}")
            return Response({"error": "Transaction failed"}, status=status.HTTP_400_BAD_REQUEST)


# Customer Verification
class VerifyCustomerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        service_id = request.data.get("service_id")
        customer_id = request.data.get("customer_id")
        variation_id = request.data.get("variation_id")

        if not service_id or not customer_id:
            return Response({"error": "service_id and customer_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        client = ClubKonnectClient()

        try:
            # Determine if it's TV or Electricity
            if service_id in ["dstv", "gotv", "startimes"]:
                resp = client.verify_tv(tv_id=service_id, smart_card_number=customer_id)
            else:
                resp = client.verify_electricity(disco_id=service_id, meter_number=customer_id)

            if resp.get("status") == "success":
                # ClubKonnect returns customer name in 'customer_name' or similar
                return Response(resp, status=status.HTTP_200_OK)
            else:
                return Response({"error": resp.get("message", "Verification failed.")}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Customer verification failed: {str(e)}")
            return Response({"error": "Verification failed."}, status=status.HTTP_400_BAD_REQUEST)


# Electricity Services
class ElectricityServiceListView(generics.ListAPIView):
    queryset = ElectricityService.objects.all()
    serializer_class = DataServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

class PurchaseElectricityView(APIView):
    permission_classes=  [permissions.IsAuthenticated]
    serializer_class = ElectricityPurchaseRequestSerializer

    def post(self, request):
        serializer = ElectricityPurchaseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]
        service_id = serializer.validated_data["service_id"]
        variation_id = serializer.validated_data["variation_id"]
        customer_id = serializer.validated_data["customer_id"]

        user = request.user

        wallet, _ = Wallet.objects.get_or_create(user=user)

        if wallet.balance < amount:
            return Response({"error": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)


        reference = generate_request_id()

        client = ClubKonnectClient()

        try:
            electricity_service = ElectricityService.objects.filter(service_id=service_id).first()
            if not electricity_service:
                return Response({"error": "Invalid Electricity Service."}, status=status.HTTP_400_BAD_REQUEST)

            resp = client.buy_electricity(
                request_id=reference, 
                disco_id=service_id, 
                plan_id=variation_id,
                meter_number=customer_id,
                phone=user.phone_number if hasattr(user, 'phone_number') else "",
                amount=amount,
            )

            if resp.get("status") == "success":
                # Step 1: Debit wallet
                debit_wallet(user.id, amount, f"Electricity purchase - {reference}")

                # Step 2: Create transaction record
                transaction = Purchase.objects.create(
                    user=user,
                    purchase_type="electricity",
                    electricity_service=electricity_service,
                    beneficiary=customer_id,
                    reference=reference,
                    amount=amount,
                    status="success"
                )
                return Response(PurchaseSerializer(transaction).data, status=status.HTTP_201_CREATED)
            else:
                return Response({"error": resp.get("message", "Transaction failed")}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Electricity purchase failed: {str(e)}")
            return Response({"error": "Transaction failed"}, status=status.HTTP_400_BAD_REQUEST)


# Cable/TV Services
class TVServicesListView(generics.ListAPIView):
    queryset = TVService.objects.all()
    serializer_class = TVServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

class TVPackagesListView(generics.ListAPIView):
    queryset = TVVariation.objects.all()
    serializer_class = TVVariationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        service_id = self.request.query_params.get("service_id")
        if not service_id:
            return TVVariation.objects.filter(is_active=True)
        return TVVariation.objects.filter(is_active=True, service__service_id=service_id)

class PurchaseTVSubscriptionView(APIView):
    permission_classes=  [permissions.IsAuthenticated]
    serializer_class = TVPurchaseRequestSerializer

    def post(self, request):
        serializer = TVPurchaseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]
        service_id = serializer.validated_data["service_id"]
        variation_id = serializer.validated_data["variation_id"]
        customer_id = serializer.validated_data["customer_id"]
        subscription_type = serializer.validated_data["subscription_type"]

        user = request.user

        wallet, _ = Wallet.objects.get_or_create(user=user)

        if wallet.balance < amount:
            return Response({"error": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)


        reference = generate_request_id()

        client = ClubKonnectClient()

        try:
            tv_variation = TVVariation.objects.filter(variation_id=variation_id).first()
            if not tv_variation:
                return Response({"error": "Invalid TV Service."}, status=status.HTTP_400_BAD_REQUEST)

            resp = client.buy_tv(
                request_id=reference, 
                tv_id=service_id, 
                package_id=variation_id,
                smart_card_number=customer_id,
                phone=user.phone_number if hasattr(user, 'phone_number') else "",
            )

            if resp.get("status") == "success":
                # Step 1: Debit wallet
                debit_wallet(user.id, amount, f"TV Subscription purchase - {reference}")

                # Step 2: Create transaction record
                transaction = Purchase.objects.create(
                    user=user,
                    purchase_type="tv",
                    tv_variation=tv_variation,
                    beneficiary=customer_id,
                    reference=reference,
                    amount=amount,
                    status="success"
                )
                return Response(PurchaseSerializer(transaction).data, status=status.HTTP_201_CREATED)
            else:
                return Response({"error": resp.get("message", "Transaction failed")}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"TV Subscription purchase failed: {str(e)}")
            return Response({"error": "Transaction failed"}, status=status.HTTP_400_BAD_REQUEST)


# Purchase History
class PurchaseHistoryView(generics.ListAPIView):
    serializer_class = PurchaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Purchase.objects.filter(user=self.request.user).order_by("-time")

class PurchaseDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            purchase = Purchase.objects.get(pk=pk, user=request.user)
        except Purchase.DoesNotExist:
            return Response({"error": "Purchase not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PurchaseSerializer(purchase)
        return Response(serializer.data, status=status.HTTP_200_OK)

