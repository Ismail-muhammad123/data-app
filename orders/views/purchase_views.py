import logging
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema
from orders.models import (
    DataVariation, AirtimeNetwork, ElectricityVariation, 
    TVVariation, InternetVariation, Purchase, EducationVariation
)
from orders.serializers import (
    DataPurchaseRequestSerializer, AirtimePurchaseRequestSerializer,
    ElectricityPurchaseRequestSerializer, TVPurchaseRequestSerializer,
    InternetPurchaseRequestSerializer, EducationPurchaseRequestSerializer,
    PurchaseSerializer, RepeatPurchaseRequestSerializer, ErrorResponseSerializer
)
from orders.utils.purchase_logic import process_vtu_purchase
from .utility_views import generate_request_id
from notifications.utils import NotificationService

logger = logging.getLogger(__name__)


class PurchaseDataVariationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Orders - Data"],
        summary="Purchase a data bundle",
        description="Buy a data plan for a specified phone number. Requires a valid transaction PIN.",
        request=DataPurchaseRequestSerializer,
        responses={201: PurchaseSerializer, 400: ErrorResponseSerializer, 403: ErrorResponseSerializer}
    )
    def post(self, request):
        serializer = DataPurchaseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        pin = serializer.validated_data.get("transaction_pin")
        if not user.check_transaction_pin(pin):
            return Response({"error": "Invalid transaction PIN."}, status=status.HTTP_403_FORBIDDEN)

        plan_id = serializer.validated_data["plan_id"]
        phone_number = serializer.validated_data["phone_number"]
        promo_code = serializer.validated_data.get("promo_code")

        try:
            plan = DataVariation.objects.get(id=plan_id, is_active=True)
        except DataVariation.DoesNotExist:
            return Response({"error": "Invalid or inactive plan."}, status=status.HTTP_400_BAD_REQUEST)

        amount = plan.agent_price if user.role == 'agent' else plan.selling_price

        reference = generate_request_id()
        result = process_vtu_purchase(
            user=user,
            purchase_type="data",
            amount=amount,
            beneficiary=phone_number,
            action="buy_data",
            promo_code_str=promo_code,
            service_name=f"{plan.service.service_name} Data Bundle",
            reference=reference,
            phone=phone_number,
            network=plan.service.service_id,
            plan_id=plan.variation_id,
            data_variation=plan
        )

        if result['status'] == "FAILED":
             NotificationService.send_push(user, "Data Purchase Failed", f"Your purchase of {plan.name} was unsuccessful. N{amount} has been refunded.")
             return Response({"error": result.get("error", "Transaction failed")}, status=status.HTTP_400_BAD_REQUEST)

        NotificationService.send_push(user, "Data Purchase Successful", f"Your purchase of {plan.name} to {phone_number} was successful.")
        return Response(PurchaseSerializer(Purchase.objects.get(id=result['purchase_id'])).data, status=status.HTTP_201_CREATED)


class PurchaseAirtimeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Orders - Airtime"],
        summary="Purchase airtime",
        description="Buy airtime for a specified phone number. Discount is applied based on user role (agent/regular).",
        request=AirtimePurchaseRequestSerializer,
        responses={201: PurchaseSerializer, 400: ErrorResponseSerializer, 403: ErrorResponseSerializer}
    )
    def post(self, request):
        serializer = AirtimePurchaseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        pin = serializer.validated_data.get("transaction_pin")
        if not user.check_transaction_pin(pin):
            return Response({"error": "Invalid transaction PIN."}, status=status.HTTP_403_FORBIDDEN)

        amount = serializer.validated_data["amount"]
        phone_number = serializer.validated_data["phone_number"]
        service_id = serializer.validated_data["service_id"]
        promo_code = serializer.validated_data.get("promo_code")

        try:
            network = AirtimeNetwork.objects.get(service_id=service_id)
        except AirtimeNetwork.DoesNotExist:
            return Response({"error": "Invalid Service."}, status=status.HTTP_400_BAD_REQUEST)

        discount_val = network.agent_discount if user.role == 'agent' else network.discount
        actual_amount = Decimal(amount) - (Decimal(amount) * Decimal(discount_val) / 100)

        reference = generate_request_id()
        result = process_vtu_purchase(
            user=user,
            purchase_type="airtime",
            amount=actual_amount,
            beneficiary=phone_number,
            action="buy_airtime",
            promo_code_str=promo_code,
            service_name=f"{network.service_name} Airtime",
            reference=reference,
            phone=phone_number,
            network=network.service_id,
            airtime_service=network
        )

        if result['status'] == "FAILED":
             NotificationService.send_push(user, "Airtime Purchase Failed", f"Your purchase of N{amount} airtime was unsuccessful. N{actual_amount} has been refunded.")
             return Response({"error": result.get("error", "Transaction failed")}, status=status.HTTP_400_BAD_REQUEST)

        NotificationService.send_push(user, "Airtime Purchase Successful", f"Your purchase of N{amount} {network.service_name} airtime to {phone_number} was successful.")
        return Response(PurchaseSerializer(Purchase.objects.get(id=result['purchase_id'])).data, status=status.HTTP_201_CREATED)


class PurchaseElectricityView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Orders - Electricity"],
        summary="Purchase electricity token",
        description="Pay for electricity for a specified meter number. Returns a token on success.",
        request=ElectricityPurchaseRequestSerializer,
        responses={201: PurchaseSerializer, 400: ErrorResponseSerializer, 403: ErrorResponseSerializer}
    )
    def post(self, request):
        serializer = ElectricityPurchaseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        pin = serializer.validated_data.get("transaction_pin")
        if not user.check_transaction_pin(pin):
            return Response({"error": "Invalid transaction PIN."}, status=status.HTTP_403_FORBIDDEN)

        amount = serializer.validated_data["amount"]
        service_id = serializer.validated_data["service_id"]
        variation_id = serializer.validated_data["variation_id"]
        customer_id = serializer.validated_data["customer_id"]
        promo_code = serializer.validated_data.get("promo_code")

        try:
            electricity_variation = ElectricityVariation.objects.get(variation_id=variation_id)
        except ElectricityVariation.DoesNotExist:
            return Response({"error": "Invalid Variation."}, status=status.HTTP_400_BAD_REQUEST)

        discount_val = electricity_variation.agent_discount if user.role == 'agent' else electricity_variation.discount
        actual_amount = Decimal(amount) - (Decimal(amount) * Decimal(discount_val) / 100)

        reference = generate_request_id()
        result = process_vtu_purchase(
            user=user,
            purchase_type="electricity",
            amount=actual_amount,
            beneficiary=customer_id,
            action="buy_electricity",
            promo_code_str=promo_code,
            service_name=f"{electricity_variation.service.service_name} Electricity",
            reference=reference,
            disco_id=service_id,
            plan_id=variation_id,
            meter_number=customer_id,
            phone=user.phone_number,
            electricity_service=electricity_variation.service,
            electricity_variation=electricity_variation
        )

        if result['status'] == "FAILED":
             NotificationService.send_push(user, "Electricity Purchase Failed", f"Your electricity purchase of N{amount} was unsuccessful. N{actual_amount} has been refunded.")
             return Response({"error": result.get("error", "Transaction failed")}, status=status.HTTP_400_BAD_REQUEST)

        NotificationService.send_push(user, "Electricity Purchase Successful", f"Your electricity purchase for meter {customer_id} was successful.")
        return Response(PurchaseSerializer(Purchase.objects.get(id=result['purchase_id'])).data, status=status.HTTP_201_CREATED)


class PurchaseTVSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Orders - Cable TV"],
        summary="Purchase TV subscription",
        description="Subscribe to a Cable TV bouquet (DSTV, GOTV, Startimes) for a specified smartcard number.",
        request=TVPurchaseRequestSerializer,
        responses={201: PurchaseSerializer, 400: ErrorResponseSerializer, 403: ErrorResponseSerializer}
    )
    def post(self, request):
        serializer = TVPurchaseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        pin = serializer.validated_data.get("transaction_pin")
        if not user.check_transaction_pin(pin):
            return Response({"error": "Invalid transaction PIN."}, status=status.HTTP_403_FORBIDDEN)

        amount = serializer.validated_data["amount"]
        service_id = serializer.validated_data["service_id"]
        variation_id = serializer.validated_data["variation_id"]
        customer_id = serializer.validated_data["customer_id"]
        promo_code = serializer.validated_data.get("promo_code")

        try:
            tv_variation = TVVariation.objects.get(variation_id=variation_id)
        except TVVariation.DoesNotExist:
            return Response({"error": "Invalid TV Service."}, status=status.HTTP_400_BAD_REQUEST)

        amount = tv_variation.agent_price if user.role == 'agent' else tv_variation.selling_price

        reference = generate_request_id()
        result = process_vtu_purchase(
            user=user,
            purchase_type="tv",
            amount=amount,
            beneficiary=customer_id,
            action="buy_tv",
            promo_code_str=promo_code,
            service_name=f"{tv_variation.service.service_name} TV Sub",
            reference=reference,
            tv_id=service_id,
            package_id=variation_id,
            smart_card_number=customer_id,
            phone=user.phone_number,
            tv_variation=tv_variation
        )

        if result['status'] == "FAILED":
             NotificationService.send_push(user, "TV Subscription Failed", "Your TV subscription was unsuccessful. Funds have been refunded.")
             return Response({"error": result.get("error", "Transaction failed")}, status=status.HTTP_400_BAD_REQUEST)

        NotificationService.send_push(user, "TV Subscription Successful", f"Your TV subscription for {customer_id} was successful.")
        return Response(PurchaseSerializer(Purchase.objects.get(id=result['purchase_id'])).data, status=status.HTTP_201_CREATED)


class PurchaseInternetSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Orders - Internet"],
        summary="Purchase Internet data subscription",
        description="Buy a Internet data package for a specified phone number.",
        request=InternetPurchaseRequestSerializer,
        responses={201: PurchaseSerializer, 400: ErrorResponseSerializer, 403: ErrorResponseSerializer}
    )
    def post(self, request):
        serializer = InternetPurchaseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        pin = serializer.validated_data.get("transaction_pin")
        if not user.check_transaction_pin(pin):
            return Response({"error": "Invalid transaction PIN."}, status=status.HTTP_403_FORBIDDEN)

        plan_id = serializer.validated_data["plan_id"]
        phone_number = serializer.validated_data["phone_number"]
        promo_code = serializer.validated_data.get("promo_code")

        try:
            plan = InternetVariation.objects.get(id=plan_id, is_active=True)
        except InternetVariation.DoesNotExist:
            return Response({"error": "Invalid Internet Package."}, status=status.HTTP_400_BAD_REQUEST)

        amount = plan.agent_price if user.role == 'agent' else plan.selling_price

        reference = generate_request_id()
        result = process_vtu_purchase(
            user=user,
            purchase_type="internet",
            amount=amount,
            beneficiary=phone_number,
            action="buy_internet",
            promo_code_str=promo_code,
            service_name="Internet Subscription",
            reference=reference,
            plan_id=plan.variation_id,
            phone=phone_number,
            internet_variation=plan
        )

        if result['status'] == "FAILED":
             NotificationService.send_push(user, "Internet Subscription Failed", "Your Internet subscription was unsuccessful. Funds have been refunded.")
             return Response({"error": result.get("error", "Transaction failed")}, status=status.HTTP_400_BAD_REQUEST)

        NotificationService.send_push(user, "Internet Subscription Successful", f"Your Internet subscription for {phone_number} was successful.")
        return Response(PurchaseSerializer(Purchase.objects.get(id=result['purchase_id'])).data, status=status.HTTP_201_CREATED)


class PurchaseEducationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Orders - Education"],
        summary="Purchase education PIN",
        description="Buy an exam PIN (WAEC, NECO, NABTEB, JAMB) for a specified exam type.",
        request=EducationPurchaseRequestSerializer,
        responses={200: PurchaseSerializer, 400: ErrorResponseSerializer, 403: ErrorResponseSerializer}
    )
    def post(self, request):
        serializer = EducationPurchaseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        amount = serializer.validated_data['amount']
        service_id = serializer.validated_data['service_id']
        variation_id = serializer.validated_data['variation_id']
        promo_code = serializer.validated_data.get('promo_code')
        pin = serializer.validated_data.get('transaction_pin')

        if not user.check_transaction_pin(pin):
            return Response({"error": "Invalid transaction PIN."}, status=status.HTTP_403_FORBIDDEN)

        try:
            plan = EducationVariation.objects.get(variation_id=variation_id, service__service_id=service_id, is_active=True)
        except EducationVariation.DoesNotExist:
            return Response({"error": "Invalid or inactive plan."}, status=status.HTTP_400_BAD_REQUEST)

        amount = plan.agent_price if user.role == 'agent' else plan.selling_price

        res = process_vtu_purchase(
            user=user,
            purchase_type="education",
            amount=amount,
            beneficiary="N/A",
            action="buy_education",
            promo_code_str=promo_code,
            service_name=f"{plan.name} PIN",
            exam_type=service_id,
            variation_id=variation_id,
            quantity=1,
            education_variation=plan
        )

        if res.get('status') == 'success':
            NotificationService.send_push(user, "Education PIN Successful", f"Your {plan.name} purchase was successful.")
            return Response(res, status=status.HTTP_200_OK)
        else:
            NotificationService.send_push(user, "Education PIN Failed", "Your education PIN purchase was unsuccessful. Funds have been refunded.")
            return Response(res, status=status.HTTP_400_BAD_REQUEST)


class RepeatPurchaseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Orders - Repeat"],
        summary="Repeat a previous purchase",
        description="Re-trigger a previous transaction by passing the original purchase ID. Requires a valid transaction PIN. The same beneficiary and plan are used.",
        request=RepeatPurchaseRequestSerializer,
        responses={201: PurchaseSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer, 403: ErrorResponseSerializer}
    )
    def post(self, request):
        serializer = RepeatPurchaseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        pin = serializer.validated_data.get("transaction_pin")
        if not user.check_transaction_pin(pin):
            return Response({"error": "Invalid transaction PIN."}, status=status.HTTP_403_FORBIDDEN)

        purchase_id = serializer.validated_data["purchase_id"]

        try:
            old_purchase = Purchase.objects.get(id=purchase_id, user=user)
        except Purchase.DoesNotExist:
            return Response({"error": "Original purchase not found."}, status=status.HTTP_404_NOT_FOUND)

        if old_purchase.purchase_type == 'data' and old_purchase.data_variation:
             if not old_purchase.data_variation.is_active or not old_purchase.data_variation.service.is_active:
                 return Response({"error": "This data plan is no longer available."}, status=status.HTTP_400_BAD_REQUEST)

        action_map = {
            'data': 'buy_data',
            'airtime': 'buy_airtime',
            'electricity': 'buy_electricity',
            'tv': 'buy_tv',
            'internet': 'buy_internet',
            'education': 'buy_education'
        }
        
        action = action_map.get(old_purchase.purchase_type)
        kwargs = {
            'reference': generate_request_id(),
            'phone': old_purchase.beneficiary,
        }

        if old_purchase.airtime_service: 
            kwargs['airtime_service'] = old_purchase.airtime_service
            kwargs['network'] = old_purchase.airtime_service.service_id
        if old_purchase.data_variation: 
            kwargs['data_variation'] = old_purchase.data_variation
            kwargs['network'] = old_purchase.data_variation.service.service_id
            kwargs['plan_id'] = old_purchase.data_variation.variation_id
        if old_purchase.tv_variation:
            kwargs['tv_variation'] = old_purchase.tv_variation
            kwargs['tv_id'] = old_purchase.tv_variation.service.service_id
            kwargs['package_id'] = old_purchase.tv_variation.variation_id
            kwargs['smart_card_number'] = old_purchase.beneficiary
        if old_purchase.electricity_variation:
            kwargs['electricity_variation'] = old_purchase.electricity_variation
            kwargs['disco_id'] = old_purchase.electricity_variation.service.service_id
            kwargs['plan_id'] = old_purchase.electricity_variation.variation_id
            kwargs['meter_number'] = old_purchase.beneficiary
        if old_purchase.internet_variation:
            kwargs['internet_variation'] = old_purchase.internet_variation
            kwargs['plan_id'] = old_purchase.internet_variation.variation_id
        if old_purchase.education_variation:
            kwargs['education_variation'] = old_purchase.education_variation
            kwargs['variation_id'] = old_purchase.education_variation.variation_id
            kwargs['exam_type'] = old_purchase.education_variation.service.service_id

        result = process_vtu_purchase(
            user=request.user,
            purchase_type=old_purchase.purchase_type,
            amount=old_purchase.amount,
            beneficiary=old_purchase.beneficiary,
            action=action,
            service_name=f"Repeated {old_purchase.purchase_type} purchase",
            **kwargs
        )

        if result['status'] == "FAILED":
            return Response({"error": result.get("error", "Transaction failed")}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PurchaseSerializer(Purchase.objects.get(id=result['purchase_id'])).data, status=status.HTTP_201_CREATED)
