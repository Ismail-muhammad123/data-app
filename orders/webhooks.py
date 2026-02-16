from .models import Purchase


def clubkonnect_callback(request):
    data = request.GET or request.POST

    order_id = data.get("orderid")
    request_id = data.get("requestid")
    status_code = data.get("statuscode")
    order_status = data.get("orderstatus")
    order_remark = data.get("orderremark")

    try:
        if order_id:
            purchase = Purchase.objects.get(order_id=order_id)
        elif request_id:
            purchase = Purchase.objects.get(reference=request_id)
        else:
            return JsonResponse({"status": "ignored", "message": "No identifier provided"})

        if status_code == "200":
            purchase.status = "success"
        elif status_code in ["100", "101", "102"]: # Pending codes
            purchase.status = "pending"
        else:
            purchase.status = "failed"

        purchase.save()

    except Purchase.DoesNotExist:
        return JsonResponse({"status": "not_found"})

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