from django.db import transaction as db_transaction
from django.utils import timezone
from decimal import Decimal
import logging

from wallet.utils import debit_wallet, fund_wallet
from orders.models import (
    Purchase, PromoCode, PurchasePromoUsed, VTUProviderConfig,
    DataService, AirtimeNetwork, ElectricityService, TVService, InternetService, EducationService, ServiceRouting, ServiceFallback
)
from orders.router import ProviderRouter
from notifications.utils import NotificationService
import uuid

logger = logging.getLogger(__name__)

def process_vtu_purchase(user, purchase_type, amount, beneficiary, action, promo_code_str=None, initiator="self", initiated_by=None, **kwargs):
    """
    Unified logic for processing VTU purchases.
    """
    service_name = kwargs.get('service_name', purchase_type.title())
    
    # 1. Handle Promo Code
    discount = Decimal('0.00')
    promo_obj = None
    if promo_code_str:
        promo_obj = PromoCode.objects.filter(code=promo_code_str).first()
        if promo_obj and promo_obj.is_valid():
            if promo_obj.discount_amount > 0:
                discount = promo_obj.discount_amount
            elif promo_obj.discount_percentage > 0:
                discount = (Decimal(amount) * promo_obj.discount_percentage) / 100
        else:
            return {"status": "FAILED", "error": "Invalid or expired promo code."}

    final_amount = Decimal(amount) - discount
    if final_amount < 0: final_amount = Decimal('0.00')

    # 2. Reference & record initialization
    reference = kwargs.get('reference')
    
    # 3. Debit Wallet
    debit_success, msg = debit_wallet(
        user.id, 
        final_amount, 
        f"{service_name} purchase: {reference}",
        initiator=initiator,
        initiated_by=initiated_by
    )
    if not debit_success:
        return {"status": "FAILED", "error": f"Wallet debit failed: {msg}"}

    # 4. Execute via Router
    res = ProviderRouter.execute_with_fallback(purchase_type, action, **kwargs)

    # 5. Handle Outcome
    status = "pending"
    if res['status'] == 'SUCCESS':
        status = "success"
    elif res['status'] == 'FAILED':
        status = "failed"

    with db_transaction.atomic():
        # Create Purchase Record
        provider_obj = None
        provider_name = res.get('provider_used')
        if provider_name:
            provider_obj = VTUProviderConfig.objects.filter(name=provider_name).first()

        purchase = Purchase.objects.create(
            user=user,
            purchase_type=purchase_type,
            amount=final_amount,
            beneficiary=beneficiary,
            reference=reference,
            status=status,
            provider_response=res,
            provider=provider_obj,
            initiator=initiator,
            initiated_by=initiated_by
        )
        
        # Link extras
        if 'airtime_service' in kwargs: purchase.airtime_service = kwargs['airtime_service']
        if 'data_variation' in kwargs: purchase.data_variation = kwargs['data_variation']
        if 'electricity_service' in kwargs: purchase.electricity_service = kwargs['electricity_service']
        if 'tv_variation' in kwargs: purchase.tv_variation = kwargs['tv_variation']
        if 'internet_variation' in kwargs: purchase.internet_variation = kwargs['internet_variation']
        if 'education_variation' in kwargs: purchase.education_variation = kwargs['education_variation']
        if res.get('token'): purchase.purchased_token = res['token']
        
        purchase.save()

        # Handle Promo Usage
        if promo_obj:
            PurchasePromoUsed.objects.create(
                purchase=purchase,
                promo_code=promo_obj,
                discount_applied=discount
            )
            promo_obj.used_count += 1
            promo_obj.save()

        # Terminal Failure - Auto Refund
        if status == "failed":
            fund_wallet(
                user.id, 
                final_amount, 
                f"Refund: {service_name} purchase failed ({reference})",
                initiator="system"
            )
            NotificationService.send_from_template(
                user, 
                "purchase-failed", 
                {"service": service_name, "beneficiary": beneficiary, "reference": reference, "amount": final_amount}
            )
        elif status == "success":
            NotificationService.send_from_template(
                user, 
                "purchase-success", 
                {"service": service_name, "beneficiary": beneficiary, "reference": reference, "amount": final_amount}
            )
            # Cashback & Referral logic
            from wallet.utils import process_cashback, process_referral_reward
            process_cashback(user, purchase_type, final_amount)
            process_referral_reward(user, trigger_event='transaction', transaction_amount=final_amount)

    return {"status": status, "purchase_id": purchase.id, "res": res}

def handle_vtu_async_failure(purchase):
    """
    Handles terminal failures reported via webhooks/callbacks.
    Decides whether to retry, fallback, or refund based on config.
    """
    logger.info(f"Handling async failure for purchase {purchase.reference}")
    
    # 1. Check if we should retry or fallback
    routing = ServiceRouting.objects.filter(service=purchase.purchase_type).first()
    provider_config = purchase.provider
    
    # Track the failure
    purchase.status = "failed"
    # We don't automatically increment retry_count here, 
    # we use it as a limit check.
    
    if routing:
        max_retries = routing.retry_count or 1
        
        # Determine current chain and where we are
        chain = ProviderRouter.get_routing_chain(purchase.purchase_type)
        provider_names = [p.provider_name for p in chain]
        
        current_index = -1
        if provider_config and provider_config.name in provider_names:
            current_index = provider_names.index(provider_config.name)

        # 2. Case: Retry with SAME provider
        if purchase.retry_count < max_retries:
            logger.info(f"Retrying purchase {purchase.reference} with same provider (Attempt {purchase.retry_count + 1})")
            purchase.retry_count += 1
            purchase.save()
            
            # Execute retry (can be async task)
            # For now, let's trigger it directly
            res = ProviderRouter.execute_with_fallback(purchase.purchase_type, "re-buy-action", reference=purchase.reference)
            # Re-buy action is pseudocode, would need specific methods like buy_airtime
            # Actually ProviderRouter handles the whole logic.

        # 3. Case: Fallback to NEXT provider
        elif current_index != -1 and current_index < len(provider_names) - 1:
            next_provider = provider_names[current_index + 1]
            logger.info(f"Falling back to provider {next_provider} for purchase {purchase.reference}")
            # ... Logic to trigger purchase with next provider ...
            # Actually, simply calling execution again with the remaining chain might be better,
            # but that's what execute_with_fallback does initially.
            # In an async fail state, we might just want to trigger a manual retry from the admin dashboard.

    # 4. Final Fallback: Refund
    if provider_config and provider_config.auto_refund_on_failure:
        fund_wallet(
            purchase.user.id, 
            purchase.amount, 
            f"Auto-Refund: Failed {purchase.purchase_type} purchase ({purchase.reference})",
            initiator="system"
        )
        NotificationService.send_from_template(
            purchase.user, 
            "transaction-reversed", 
            {"service": purchase.purchase_type, "beneficiary": purchase.beneficiary, "reference": purchase.reference, "amount": purchase.amount}
        )
    
    purchase.save()
    return True
