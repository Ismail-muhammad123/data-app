import logging
import json
from django.http import JsonResponse
from django.db import transaction as db_transaction
from .models import Purchase
from .services.clubkonnect import ClubKonnectClient
from wallet.utils import fund_wallet

logger = logging.getLogger(__name__)

from .router import ProviderRouter

def vtu_webhook(request, provider_name):
    """Generic webhook handler for all VTU providers."""
    try:
        data = json.loads(request.body.decode("utf-8")) if request.method == "POST" else request.GET.dict()
        logger.info(f"Webhook received from {provider_name}: {data}")
        
        provider = ProviderRouter.get_provider_implementation(provider_name)
        if provider:
            provider.handle_webhook(data)
            return JsonResponse({"status": "SUCCESS", "message": "Webhook processed"})
        
        return JsonResponse({"status": "NOT_FOUND", "message": f"Provider {provider_name} implementation not found"}, status=404)
    except Exception as e:
        logger.error(f"Error in vtu_webhook for {provider_name}: {e}")
        return JsonResponse({"status": "ERROR", "message": str(e)}, status=500)

def vtu_callback(request, provider_name):
    """Generic callback handler for all VTU providers."""
    try:
        data = request.POST.dict() if request.method == "POST" else request.GET.dict()
        logger.info(f"Callback received from {provider_name}: {data}")
        
        provider = ProviderRouter.get_provider_implementation(provider_name)
        if provider:
            provider.handle_callback(data)
            return JsonResponse({"status": "SUCCESS", "message": "Callback processed"})
            
        return JsonResponse({"status": "NOT_FOUND", "message": f"Provider {provider_name} implementation not found"}, status=404)
    except Exception as e:
        logger.error(f"Error in vtu_callback for {provider_name}: {e}")
        return JsonResponse({"status": "ERROR", "message": str(e)}, status=500)

def clubkonnect_callback(request):
    """
    Callback handler for ClubKonnect transactions.
    Supports both query string and JSON body payloads.
    """
    if request.method == "POST":
        try:
            # Try to parse JSON body if POST
            data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fallback to POST parameters
            data = request.POST.dict()
    else:
        # GET query string
        data = request.GET.dict()

    logger.info(f"ClubKonnect callback received: {data}")

    print("Webhook data: ", data)
    order_id = data.get("orderid")
    request_id = data.get("requestid")
    status_code = data.get("statuscode")
    order_remark = data.get("orderremark")

    try:
        # Find the purchase record (Reference is the OrderID)
        purchase = Purchase.objects.filter(reference__in=[order_id, request_id]).first()
        
        if not purchase:
            logger.warning(f"Purchase not found for callback: order_id={order_id}, request_id={request_id}")
            return JsonResponse({"status": "not_found"}, status=404)

        # Update purchase details
        purchase.provider_response = data

        # Map Status Codes
        terminal_failure = False
        
        if status_code == "200":
            purchase.status = "success"
        elif status_code in ["100", "101", "102"]:
            purchase.status = "pending"
        else:
            purchase.status = "failed"
            terminal_failure = True

        with db_transaction.atomic():
            purchase.save()

            # Handle Fund Reversal on Failure
            if terminal_failure:
                # 1. Send Cancel Request first (reference is RequestID)
                client = ClubKonnectClient()
                cancel_resp = client.cancel_transaction(request_id=purchase.reference)
                logger.info(f"Cancel request for failed purchase {purchase.reference}: {cancel_resp}")
                
                # Update response to include cancel details
                purchase.provider_response["cancel_request_response"] = cancel_resp
                purchase.save()

                # 2. Reverse funds to user wallet
                logger.info(f"Initiating fund reversal for failed purchase {purchase.reference}")
                fund_wallet(
                    user_id=purchase.user.id,
                    amount=purchase.amount,
                    description=f"Refund: Failed {purchase.purchase_type} purchase ({purchase.reference})",
                )

    except Exception as e:
        logger.exception(f"Error handling ClubKonnect callback: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "received"})



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