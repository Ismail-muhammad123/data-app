import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics

from orders.models import DataNetwork, DataPlan, DataSale, AirtimeNetwork, AirtimeSale
from orders.utils import purchase_service
from wallet.utils import debit_wallet
from .serializers import DataNetworkSerializer, DataPlanSerializer, DataSaleSerializer, AirtimeNetworkSerializer, AirtimeSaleSerializer
import logging
from django.utils.dateparse import parse_date

logger = logging.getLogger(__name__)



# # ---------- ADMIN CRUD ----------
# class PlanListCreateView(generics.ListCreateAPIView):
#     queryset = Plan.objects.all()
#     serializer_class = PlanSerializer
#     permission_classes = [permissions.IsAdminUser]


# class PlanDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Plan.objects.all()
#     serializer_class = PlanSerializer
#     permission_classes = [permissions.IsAdminUser]



# class AllPlanTransactionsView(generics.ListAPIView):
#     queryset = PlanTransaction.objects.all().order_by("-created_at")
#     serializer_class = PlanTransactionSerializer
#     permission_classes = [permissions.IsAdminUser]

#     def get_queryset(self):
#         queryset = PlanTransaction.objects.all().order_by("-created_at")

#         # Filter by date range
#         start_date = self.request.query_params.get("start")
#         end_date = self.request.query_params.get("end")
#         if start_date:
#             queryset = queryset.filter(created_at__date__gte=parse_date(start_date))
#         if end_date:
#             queryset = queryset.filter(created_at__date__lte=parse_date(end_date))

#         # Filter by service_type (network: airtime/data/smile)
#         network = self.request.query_params.get("network")
#         if network:
#             queryset = queryset.filter(plan__service_type=network)

#         return queryset


# class PlanTransactionsByPlanView(generics.ListAPIView):
#     serializer_class = PlanTransactionSerializer
#     permission_classes = [permissions.IsAdminUser]

#     def get_queryset(self):
#         plan_id = self.kwargs.get("plan_id")
#         queryset = PlanTransaction.objects.filter(plan_id=plan_id).order_by("-created_at")

#         # 🔹 Date range filters
#         start_date = self.request.query_params.get("start")
#         end_date = self.request.query_params.get("end")
#         if start_date:
#             queryset = queryset.filter(created_at__date__gte=parse_date(start_date))
#         if end_date:
#             queryset = queryset.filter(created_at__date__lte=parse_date(end_date))

#         return queryset


# ---------- CUSTOMER ----------
# class PlansListView(generics.ListAPIView):
#     queryset = Plan.objects.all()
#     serializer_class = PlanSerializer
#     permission_classes = [permissions.IsAuthenticated]


# class PurchasePlanView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request):
#         serializer = PurchaseRequestSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         plan_id = serializer.validated_data["plan_id"]
#         phone_number = serializer.validated_data["phone_number"]

#         try:
#             plan = Plan.objects.get(id=plan_id, is_active=True)
#         except Plan.DoesNotExist:
#             return Response({"error": "Invalid or inactive plan."}, status=status.HTTP_400_BAD_REQUEST)

#         user = request.user
#         amount = plan.selling_price
#         reference = str(uuid.uuid4())

#         # Step 1: Debit wallet
#         wallet_debit = debit_wallet(user.id, amount, f"{plan.service_type} purchase - {reference}")
#         if not wallet_debit:
#             return Response({"error": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)

#         # Step 2: Create transaction record
#         transaction = PlanTransaction.objects.create(
#             user=user,
#             plan=plan,
#             phone_number=phone_number,
#             reference=reference,
#             amount=amount,
#             status="pending"
#         )

#         # Step 3: Call VTPass
#         vtpass_response = purchase_service(
#             service_id=plan.service_id,
#             phone_number=phone_number,
#             amount=amount,
#             request_id=reference,
#         )

#         transaction.response_data = vtpass_response

#         if vtpass_response.get("code") == "000":  # success
#             transaction.status = "success"
#         else:
#             transaction.status = "failed"

#         transaction.save()

#         return Response(PlanTransactionSerializer(transaction).data, status=status.HTTP_201_CREATED)


# class PlanTransactionsView(generics.ListAPIView):
#     serializer_class = PlanTransactionSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         return PlanTransaction.objects.filter(user=self.request.user).order_by("-created_at")




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
