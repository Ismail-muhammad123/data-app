import requests
import json
import logging
from typing import Dict, Any, Optional, List
from ..interfaces import BaseVTUProvider

logger = logging.getLogger(__name__)

class ClubKonnectProvider(BaseVTUProvider):
    """
    ClubKonnect implementation of BaseVTUProvider.
    """

    def __init__(self, config: Dict[str, Any]):
        self.user_id = config.get('user_id')
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url')
        if self.base_url is None or self.base_url == '':
            self.base_url = 'https://www.nellobytesystems.com'
            
        self.headers = {
            "Content-Type": "application/json",
        }

    @property
    def provider_name(self) -> str:
        return "clubkonnect"

    @classmethod
    def get_supported_services(cls) -> List[str]:
        return ["airtime", "data", "tv", "electricity", "internet"]

    @classmethod
    def get_config_requirements(cls) -> List[Dict[str, Any]]:
        return [
            {"name": "user_id", "label": "User ID", "type": "text", "required": True},
            {"name": "api_key", "label": "API Key", "type": "text", "required": True},
            {"name": "base_url", "label": "Base URL", "type": "text", "required": False, "default": "https://www.nellobytesystems.com"},
        ]

    def _get(self, endpoint: str, params: dict) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        params.update({"UserID": self.user_id, "APIKey": self.api_key})
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ClubKonnect request error: {str(e)}")
            raise Exception(f"ClubKonnect API error: {str(e)}")

    def buy_airtime(self, phone: str, network: str, amount: float, reference: str) -> Dict[str, Any]:
        # network map for ClubKonnect
        network_map = {'mtn': '01', 'glo': '02', 'airtel': '03', '9mobile': '04'}
        service_id = network_map.get(network.lower(), '01')
        
        params = {
            "MobileNetwork": service_id,
            "Amount": int(amount),
            "MobileNumber": phone,
            "RequestID": reference
        }
        res = self._get("/Airtime.asp", params)
        
        status = "PENDING"
        if res.get('status') == 'ORDER_COMPLETED':
            status = "SUCCESS"
        elif res.get('status') in ['ORDER_FAILED', 'ORDER_CANCELLED']:
            status = "FAILED"
            
        return {
            "status": status,
            "provider_reference": res.get('orderid'),
            "message": res.get('remark'),
            "raw_response": res
        }

    def buy_data(self, phone: str, network: str, plan_id: str, amount: float, reference: str) -> Dict[str, Any]:
        network_map = {'mtn': '01', 'glo': '02', 'airtel': '03', '9mobile': '04'}
        service_id = network_map.get(network.lower(), '01')
        
        params = {
            "MobileNetwork": service_id,
            "DataPlan": plan_id,
            "MobileNumber": phone,
            "RequestID": reference
        }
        res = self._get("/Data.asp", params)
        
        status = "PENDING"
        if res.get('status') == 'ORDER_COMPLETED':
            status = "SUCCESS"
        elif res.get('status') in ['ORDER_FAILED', 'ORDER_CANCELLED']:
            status = "FAILED"
            
        return {
            "status": status,
            "provider_reference": res.get('orderid'),
            "message": res.get('remark'),
            "raw_response": res
        }

    def pay_bill(self, service_type: str, identifier: str, amount: float, plan_id: str, reference: str, metadata: dict = None) -> Dict[str, Any]:
        # service_type for CK usually includes 'CableTV', 'Electricity'
        params = {
            "MobileNumber": identifier,
            "Amount": int(amount),
            "RequestID": reference
        }
        # CK uses different endpoints for different services
        if service_type.lower() in ['dstv', 'gotv', 'startimes']:
             endpoint = "/CableTV.asp"
             params.update({"CableTV": service_type, "Package": plan_id})
        else:
             endpoint = "/Electricity.asp"
             params.update({"ElectricCompany": service_id, "MeterNo": identifier, "MeterType": "01"}) # PREPAID

        res = self._get(endpoint, params)
        
        status = "PENDING"
        if res.get('status') == 'ORDER_COMPLETED':
            status = "SUCCESS"
        elif res.get('status') in ['ORDER_FAILED', 'ORDER_CANCELLED']:
            status = "FAILED"
            
        return {
            "status": status,
            "provider_reference": res.get('orderid'),
            "message": res.get('remark'),
            "raw_response": res
        }

    def query_transaction(self, reference: str) -> Dict[str, Any]:
        res = self._get("/Query.asp", {"RequestID": reference})
        
        status = "PENDING"
        if res.get('status') == 'ORDER_COMPLETED':
            status = "SUCCESS"
        elif res.get('status') in ['ORDER_FAILED', 'ORDER_CANCELLED']:
            status = "FAILED"
            
        return {
            "status": status,
            "raw_response": res
        }

    def handle_webhook(self, data: Dict[str, Any]) -> bool:
        """Processes ClubKonnect webhook notifications."""
        return self._process_async_feedback(data)

    def handle_callback(self, data: Dict[str, Any]) -> bool:
        """Processes ClubKonnect callback notifications."""
        return self._process_async_feedback(data)

    def _process_async_feedback(self, data: Dict[str, Any]) -> bool:
        """Unified processing for ClubKonnect async feedback."""
        from orders.models import Purchase
        
        order_id = data.get("orderid") or data.get("OrderID")
        request_id = data.get("requestid") or data.get("RequestID")
        status_code = data.get("statuscode") or data.get("StatusCode") or data.get("Status")
        
        logger.info(f"ClubKonnect Async Feedback: order_id={order_id}, request_id={request_id}, status={status_code}")

        try:
            purchase = Purchase.objects.filter(reference__in=[order_id, request_id]).first()
            if not purchase:
                logger.warning(f"ClubKonnect Feedback: Purchase not found for reference {order_id or request_id}")
                return False

            purchase.provider_response = data
            
            if status_code in ["200", "delivered", "Success"]:
                purchase.status = "success"
                purchase.save()
            elif status_code in ["100", "101", "102", "pending", "Pending"]:
                # Keep as pending
                pass
            else:
                self._handle_async_failure(purchase, f"ClubKonnect reported failure: {status_code}")

            return True
        except Exception as e:
            logger.error(f"ClubKonnect Feedback Error: {e}")
            return False

    def _handle_async_failure(self, purchase, error_msg):
        """Internal failure handling delegating to common logic."""
        purchase.last_error = error_msg
        purchase.save()
        
        from orders.utils.purchase_logic import handle_vtu_async_failure
        handle_vtu_async_failure(purchase)

    def validate_meter(self, meter_number: str, service: str) -> Dict[str, Any]:
        params = {"ElectricCompany": service, "MeterNo": meter_number}
        res = self._get("/ElectricityVerify.asp", params)
        return {
            "account_name": res.get('customername'),
            "raw_response": res
        }

    def validate_cable_id(self, card_number: str, service: str) -> Dict[str, Any]:
        params = {"CableTV": service, "SmartCardNo": card_number}
        res = self._get("/CableTVVerify.asp", params)
        return {
            "account_name": res.get('customername'),
            "raw_response": res
        }

    def get_wallet_balance(self) -> float:
        res = self._get("/APIWalletBalanceV1.asp", {})
        return res.get('balance', 0)

    def get_available_services(self) -> List[Dict[str, Any]]:
        """
        Returns a list of available services, networks, and variations from ClubKonnect.
        """
        return [
            {"type": "airtime", "endpoint": "/AirtimeNetworks.asp"},
            {"type": "data", "endpoint": "/DataPlans.asp"},
            {"type": "cable", "endpoint": "/CableTVPackages.asp"},
            {"type": "electricity", "endpoint": "/ElectricityCompanies.asp"},
            # {"type": "internet", "endpoint": "/SmilePackages.asp"},
        ]
    def get_airtime_networks(self) -> List[Dict[str, Any]]:
        res = self._get("/APIAirtimeDiscountV2.asp", {})
        return res if isinstance(res, list) else res.get('content', [])

    def get_data_plans(self, network_id: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"MobileNetwork": network_id} if network_id else {}
        res = self._get("/DataPlans.asp", params)
        return res if isinstance(res, list) else res.get('content', [])

    def get_cable_tv_packages(self, service_id: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"CableTV": service_id} if service_id else {}
        res = self._get("/CableTVPackages.asp", params)
        return res if isinstance(res, list) else res.get('content', [])

    def get_electricity_services(self) -> List[Dict[str, Any]]:
        res = self._get("/ElectricityCompanies.asp", {})
        return res if isinstance(res, list) else res.get('content', [])

    def get_internet_packages(self) -> List[Dict[str, Any]]:
        res = self._get("/SmilePackages.asp", {})
        return res if isinstance(res, list) else res.get('content', [])

    def get_education_services(self) -> List[Dict[str, Any]]:
        return []
