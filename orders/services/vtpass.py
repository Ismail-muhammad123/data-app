import requests
import logging
from django.conf import settings
from orders.models import VTUProviderConfig, Purchase
from wallet.utils import fund_wallet

logger = logging.getLogger(__name__)

class VTPassClient:
    def __init__(self, config=None):
        if config is None:
            self.provider_config = VTUProviderConfig.objects.filter(name='vtpass', is_active=True).first()
            cfg_data = self.provider_config.get_config() if self.provider_config else {}
        else:
            self.provider_config = config
            cfg_data = config.get_config()

        self.api_key = cfg_data.get('api_key')
        self.public_key = cfg_data.get('public_key')
        self.base_url = cfg_data.get('base_url') or "https://vtpass.com/api"

    def handle_webhook(self, data):
        """Processes VTpass webhook notifications."""
        request_id = data.get("requestId")
        status_ = data.get("content", {}).get("transactions", {}).get("status")
        
        logger.info(f"VTPass Webhook Processing: requestId={request_id}, status={status_}")
        
        try:
            purchase = Purchase.objects.filter(reference=request_id).first()
            if not purchase:
                logger.warning(f"VTPass Webhook: Purchase not found for reference {request_id}")
                return False

            purchase.provider_response = data
            
            if status_ == "delivered":
                purchase.status = "success"
                purchase.save()
            elif status_ in ["failed", "reversed"]:
                self._handle_failure(purchase, f"VTPass reported: {status_}")
            
            return True
        except Exception as e:
            logger.error(f"VTPass Webhook Error: {e}")
            return False

    def handle_callback(self, data):
        """Processes VTpass callback redirects (usually GET)."""
        logger.info(f"VTPass Callback Processing: {data}")
        # Callback usually just contains basic info, or we query status
        return True

    def _handle_failure(self, purchase, error_msg):
        """Internal failure handling with config checks."""
        purchase.status = "failed"
        purchase.last_error = error_msg
        purchase.save()

        if self.provider_config:
            # 1. Check for Auto-Refund
            if self.provider_config.auto_refund_on_failure:
                logger.info(f"VTPass: Initiating auto-refund for purchase {purchase.reference}")
                fund_wallet(
                    user_id=purchase.user.id,
                    amount=purchase.amount,
                    description=f"Auto-Refund: Failed {purchase.purchase_type} purchase ({purchase.reference})",
                )
            
            # 2. Check for Retry configuration (if any planned)
            # if purchase.retry_count < self.provider_config.max_retries:
            #     # Trigger retry logic here
            #     pass

    # ... Other methods can be added as needed ...
