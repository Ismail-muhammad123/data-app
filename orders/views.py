import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics

from orders.models import DataService, DataVariation, ElectricityService, Purchase, AirtimeNetwork, TVService, TVVariation
# from orders.utils import buy_airtime, buy_data_plan
from orders.utils.ebills_client import EBillsClient
from wallet.models import Wallet
from wallet.utils import debit_wallet, fund_wallet
from .serializers import (
    AirtimePurchaseRequestSerializer, 
    DataNetworkSerializer, 
    DataPlanSerializer, 
    DataPurchaseRequestSerializer,
    ElectricityPurchaseRequestSerializer, 
    PurchaseSerializer, 
    AirtimeNetworkSerializer,
    TVPurchaseRequestSerializer
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
class DataNetworksListView(generics.ListAPIView):
    queryset = DataService.objects.all()
    serializer_class = DataNetworkSerializer
    permission_classes = [permissions.IsAuthenticated]

class DataPlansListView(generics.ListAPIView):
    queryset = DataVariation.objects.all()
    serializer_class = DataPlanSerializer
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

class PurchaseDataPlanView(APIView):
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


        client = EBillsClient()

        try:
            # Authenticate
            client.authenticate()

            resp = client.buy_data(request_id=reference, 
                                phone=phone_number, 
                                service_id=plan.service.service_id, 
                                variation_id=plan.variation_id)

            
            if resp.get("code") == "success":  # success
                
                # if resp.get("message") not in ["ORDER COMPLETED", "ORDER PROCESSING"]: 
                #     return Response({"error": "Payment failed."}, status=status.HTTP_400_BAD_REQUEST)

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
                # transaction.status = "failed"
                # fund_wallet(user.id, amount, f"Refund for failed {plan.service_type} purchase - {reference}")
                return Response({"error": "Transaction failed"}, status=status.HTTP_400_BAD_REQUEST)
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

        client = EBillsClient()

        try:

            # Authenticate
            client.authenticate()

            resp = client.buy_airtime(
                request_id=reference, 
                phone=phone_number, 
                service_id=network.service_id, 
                amount=amount,
            )

            if resp.get("code") == "success" and resp.get("message") in ["ORDER PROCESSING", "ORDER COMPLETED"]:  # success
                
                # Step 1: Debit wallet
                debit_wallet(user.id, amount, f"{network} Airtime purchase - {reference}")
                
                # Step 2: Create transaction record
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
                return Response({"error": "Transaction failed"}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Airtime purchase failed: {str(e)}")
            return Response({"error": "Transaction failed"}, status=status.HTTP_400_BAD_REQUEST)


# Customer Verification
class VerifyCustomerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        service_id = request.query_params.get("service_id")
        customer_id = request.query_params.get("customer_id")
        variation_id = request.query_params.get("variation_id")

        if not service_id or not customer_id:
            return Response({"error": "service_id and customer_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        client = EBillsClient()

        try:
            # Authenticate
            client.authenticate()

            resp = client.verify_user(
                service_id=service_id,
                customer_id=customer_id,
                variation_id=variation_id
            )

            if resp.get("code") == "success":
                return Response({"customer_name": resp["data"]}, status=status.HTTP_200_OK)
            else:
                return Response({"error": resp.get("message", "Verification failed.")}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Customer verification failed: {str(e)}")
            return Response({"error": "Verification failed."}, status=status.HTTP_400_BAD_REQUEST)


# Electricity Services
class ElectricityServiceListView(generics.ListAPIView):
    queryset = ElectricityService.objects.all()
    serializer_class = DataNetworkSerializer
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

        client = EBillsClient()

        try:
            # Authenticate
            client.authenticate()

            electricity_service = ElectricityService.objects.filter(service_id=service_id).first()
            if not electricity_service:
                return Response({"error": "Invalid Electricity Service."}, status=status.HTTP_400_BAD_REQUEST)

            resp = client.pay_electricity_bill(
                request_id=reference, 
                service_id=service_id, 
                variation_id=variation_id,
                customer_id=customer_id,
                amount=amount,
            )



            if resp.get("code") == "success":  # success
                
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
                return Response({"error": "Transaction failed"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Electricity purchase failed: {str(e)}")
            return Response({"error": "Transaction failed"}, status=status.HTTP_400_BAD_REQUEST)


# Cable/TV Services
class TVVariationsListView(generics.ListAPIView):
    queryset = DataVariation.objects.all()
    serializer_class = DataPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = DataVariation.objects.filter(is_active=True)
        service_id = self.request.query_params.get("service_id")
        if service_id:
            queryset = queryset.filter(service__id=service_id)

        return queryset

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

        client = EBillsClient()

        try:
            # Authenticate
            client.authenticate()

            tv_variation = TVVariation.objects.filter(variation_id=variation_id).first()
            if not tv_variation:
                return Response({"error": "Invalid TV Service."}, status=status.HTTP_400_BAD_REQUEST)

            resp = client.pay_tv_subscription(
                request_id=reference, 
                service_id=service_id, 
                customer_id=customer_id,
                subscription_type=subscription_type,
                variation_id=variation_id,
                amount=amount,
            )

            if resp.get("code") == "success":  # success
                
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
                return Response({"error": "Transaction failed"}, status=status.HTTP_400_BAD_REQUEST)
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


# class VTpassWebhookView(APIView):
#     """
#     Endpoint for VTpass to notify transaction status updates.
#     """

#     authentication_classes = []  # VTpass doesn't send auth, usually open
#     permission_classes = []      # Make sure you add extra security later (like IP whitelist or signature check)

#     def post(self, request):
#         data = request.data
#         logger.info(f"VTpass Webhook received: {data}")

#         # Example payload from VTpass:
#         # {
#         #   "requestId": "xxxx-xxxx",
#         #   "transactionId": "123456",
#         #   "status": "delivered",  # or "failed", "pending"
#         #   "amount": "500",
#         #   "paid_amount": "500",
#         #   "transaction_date": "2023-08-12 10:34:21",
#         #   "phone": "08012345678",
#         #   "serviceID": "mtn",
#         #   "product_name": "MTN VTU",
#         # }

#         try:
#             request_id = data.get("requestId")
#             status_ = data.get("status")
#             amount = data.get("amount")
#             phone = data.get("phone")
#             service = data.get("serviceID")

#             # 🔹 TODO: Look up your local Transaction model by requestId
#             # transaction = Transaction.objects.get(request_id=request_id)
#             # transaction.status = status_
#             # transaction.save()

#             # 🔹 If it's wallet funding or cashback, credit the user's wallet
#             # wallet.credit(amount)

#             return Response(
#                 {"message": "Webhook processed successfully"},
#                 status=status.HTTP_200_OK
#             )
#         except Exception as e:
#             logger.error(f"Error handling VTpass webhook: {str(e)}")
#             return Response({"error": "Webhook processing failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# data = {
#     'code': '000', 
#     'content': {
#         'transactions': {
#             'status': 'delivered', 
#             'product_name': 'MTN Airtime VTU', 
#             'unique_element': '08011111111', 
#             'unit_price': '50', 
#             'quantity': 1, 
#             'service_verification': None, 
#             'channel': 'api', 
#             'commission': 1.7500000000000002, 
#             'total_amount': 48.25, 
#             'discount': None, 
#             'type': 'Airtime Recharge', 
#             'email': 'ismaeelmuhammad123@gmail.com', 
#             'phone': '08163351109', 
#             'name': None, 
#             'convinience_fee': 0, 
#             'amount': '50', 
#             'platform': 'api', 
#             'method': 'api', 
#             'transactionId': '17596192814965745110120424', 
#             'commission_details': {
#                 'amount': 1.7500000000000002, 
#                 'rate': '3.50', 
#                 'rate_type': 'percent', 
#                 'computation_type': 'default'
#             }
#         }
#     }, 
#     'response_description': 'TRANSACTION SUCCESSFUL', 
#     'requestId': '689b739f-676c-488a-8246-238d0c957816', 
#     'amount': 50, 
#     'transaction_date': '2025-10-04T23:08:01.000000Z', 
#     'purchased_code': ''
# }