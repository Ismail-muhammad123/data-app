import requests
import logging
from django.conf import settings
from orders.models import VTUProviderConfig, Purchase
from wallet.utils import fund_wallet
from orders.services.base import VTUInterface

logger = logging.getLogger(__name__)

class VTPassClient(VTUInterface):
    def __init__(self, config=None):
        if config is None:
            self.provider_config = VTUProviderConfig.objects.filter(name='vtpass', is_active=True).first()
            cfg_data = self.provider_config.get_config_dict() if self.provider_config else {}
        else:
            self.provider_config = config
            cfg_data = config.get_config_dict()

        self.api_key = cfg_data.get('api_key')
        self.public_key = cfg_data.get('public_key')
        self.base_url = cfg_data.get('base_url') or "https://vtpass.com/api"

    def get_balance(self):
        url = f"{self.base_url}/balance"
        headers = {"api-key": self.api_key, "public-key": self.public_key}
        try:
            resp = requests.get(url, headers=headers)
            return resp.json()
        except: return {}

    def get_available_services(self) -> list:
        return ["airtime", "data", "tv", "electricity", "education"]

    def get_config_requirements(self) -> list:
        return [
            {"key": "base_url", "label": "API Base URL", "type": "url", "required": True},
            {"key": "api_key", "label": "API Key", "type": "password", "required": True},
            {"key": "public_key", "label": "Public Key", "type": "text", "required": True},
        ]

    def buy_airtime(self, network_id, amount, phone, request_id):
        # Implementation for VTpass...
        pass

    def buy_data(self, network_id, plan_id, phone, request_id):
        pass

    def buy_tv(self, tv_id, package_id, smart_card_number, phone, request_id):
        pass

    def buy_electricity(self, disco_id, plan_id, meter_number, phone, amount, request_id):
        pass

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
        return True

    def _handle_failure(self, purchase, error_msg):
        """Internal failure handling with config checks."""
        purchase.status = "failed"
        purchase.last_error = error_msg
        purchase.save()

        if self.provider_config:
            if self.provider_config.auto_refund_on_failure:
                logger.info(f"VTPass: Initiating auto-refund for purchase {purchase.reference}")
                fund_wallet(
                    user_id=purchase.user.id,
                    amount=purchase.amount,
                    description=f"Auto-Refund: Failed {purchase.purchase_type} purchase ({purchase.reference})",
                )
