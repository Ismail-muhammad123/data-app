from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from orders.models import (
    Purchase, AirtimeNetwork, DataVariation, 
    ElectricityService, TVVariation, InternetVariation, 
    EducationVariation, ElectricityVariation
)
from orders.utils.purchase_logic import process_vtu_purchase
from ..authentication import APIKeyAuthentication
from ..permissions import IsDeveloperUser
import uuid

class DeveloperPurchaseView(generics.CreateAPIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsDeveloperUser]

    def post(self, request, *args, **kwargs):
        user = request.user
        mode = request.mode
        data = request.data
        
        purchase_type = data.get('service_type')
        beneficiary = data.get('beneficiary')
        amount = data.get('amount')
        
        if not all([purchase_type, beneficiary, amount]):
            return Response({"error": "Missing required fields: service_type, beneficiary, amount"}, status=400)

        # Sandbox Mode: Simulate success without hitting real providers or debiting real wallet
        if mode == 'sandbox':
            ref = f"SBX-{uuid.uuid4().hex[:10].upper()}"
            return Response({
                "status": "success",
                "message": "Sandbox transaction successful (Simulated)",
                "reference": ref,
                "amount": float(amount),
                "beneficiary": beneficiary,
                "mode": "sandbox"
            }, status=201)

        # Live Mode: Process regular purchase
        ref = data.get('reference', f"DEV-{uuid.uuid4().hex[:10].upper()}")
        
        # Prepare specific kwargs based on type
        vtu_kwargs = {'reference': ref, 'initiator': 'api', 'initiated_by': user}
        
        try:
            if purchase_type == 'airtime':
                network_id = data.get('network_id')
                network = get_object_or_404(AirtimeNetwork, id=network_id)
                # Apply role-based discount for airtime
                discount_val = network.agent_discount if user.role == 'agent' else network.discount
                actual_amount = float(amount) - (float(amount) * float(discount_val) / 100)
                amount = actual_amount
                vtu_kwargs.update({'airtime_service': network, 'network': network.service_id, 'action': 'buy_airtime', 'service_name': f"{network.service_name} Airtime"})
            
            elif purchase_type == 'data':
                plan_id = data.get('plan_id')
                plan = get_object_or_404(DataVariation, id=plan_id)
                amount = plan.agent_price if user.role == 'agent' else plan.selling_price
                vtu_kwargs.update({'data_variation': plan, 'network': plan.service.service_id, 'plan_id': plan.variation_id, 'action': 'buy_data', 'service_name': f"{plan.name} Data"})
            
            elif purchase_type == 'tv':
                variation_id = data.get('variation_id')
                variation = get_object_or_404(TVVariation, id=variation_id)
                amount = variation.agent_price if user.role == 'agent' else variation.selling_price
                vtu_kwargs.update({'tv_variation': variation, 'tv_id': variation.service.service_id, 'package_id': variation.variation_id, 'smart_card_number': beneficiary, 'action': 'buy_tv', 'service_name': f"{variation.name} TV"})
            
            elif purchase_type == 'electricity':
                variation_id = data.get('variation_id')
                variation = get_object_or_404(ElectricityVariation, id=variation_id)
                discount_val = variation.agent_discount if user.role == 'agent' else variation.discount
                actual_amount = float(amount) - (float(amount) * float(discount_val) / 100)
                amount = actual_amount
                vtu_kwargs.update({'electricity_variation': variation, 'disco_id': variation.service.service_id, 'plan_id': variation.variation_id, 'meter_number': beneficiary, 'action': 'buy_electricity', 'service_name': f"{variation.name} Electricity"})
            
            # Execute purchase
            result = process_vtu_purchase(user, purchase_type, amount, beneficiary, **vtu_kwargs)
            
            return Response({
                "status": result['status'],
                "reference": ref,
                "purchase_id": result.get('purchase_id'),
                "message": "Transaction initiated" if result['status'] == 'pending' else "Transaction successful" if result['status'] == 'success' else "Transaction failed",
                "error": result.get('error') if result['status'] == 'failed' else None
            }, status=status.HTTP_201_CREATED if result['status'] != 'failed' else status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

class DeveloperVerifyPurchaseView(generics.RetrieveAPIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsDeveloperUser]

    def get(self, request, reference):
        purchase = get_object_or_404(Purchase, reference=reference, user=request.user)
        return Response({
            "reference": purchase.reference,
            "status": purchase.status,
            "amount": float(purchase.amount),
            "beneficiary": purchase.beneficiary,
            "type": purchase.purchase_type,
            "created_at": purchase.time,
            "remarks": purchase.remarks
        })
