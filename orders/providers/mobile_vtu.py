import requests
import logging
import time
from typing import Dict, Any, List, Optional
from ..interfaces import BaseVTUProvider

logger = logging.getLogger(__name__)

class MobileVTUProvider(BaseVTUProvider):
    """
    MobileVTU implementation of BaseVTUProvider.
    Documentation: https://mobilevtu.com/mobile-topup-api.php
    """

    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get('api_key')
        self.api_token = config.get('api_token')
        url = config.get('base_url')
        if url:
            self.base_url = url.rstrip('/')
        else:
            self.base_url = 'https://api.mobilevtu.com/v1'

    @property
    def provider_name(self) -> str:
        return "mobilevtu"

    @classmethod
    def get_supported_services(cls) -> List[str]:
        return ['airtime', 'data']

    @classmethod
    def get_config_requirements(cls) -> List[Dict[str, Any]]:
        return [
            {'name': 'api_key', 'label': 'API Key', 'type': 'text', 'required': True, 'help_text': 'Found in your Mobilevtu account under Developers.'},
            {'name': 'api_token', 'label': 'API Token', 'type': 'text', 'required': True, 'help_text': 'Found in your Mobilevtu account under Developers.'},
            {'name': 'base_url', 'label': 'Base URL', 'type': 'text', 'required': False, 'default': 'https://api.mobilevtu.com/v1'}
        ]

    def _post(self, endpoint: str, data: dict, reference: str = None) -> Dict[str, Any]:
        """
        MobileVTU requires POST requests with specific headers and Form-Encoded data.
        """
        url = f"{self.base_url}/{self.api_key}/{endpoint.lstrip('/')}"
        
        # Request-Id must be unique for each request. Using reference or timestamp.
        request_id = reference if reference else str(int(time.time() * 1000))
        
        headers = {
            "Api-Token": self.api_token,
            "Request-Id": request_id,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            response = requests.post(url, data=data, headers=headers, timeout=30)
            return response.json()
        except Exception as e:
            logger.error(f"MobileVTU request error: {str(e)}")
            raise Exception(f"MobileVTU API error: {str(e)}")

    def buy_airtime(self, phone: str, network: str, amount: float, reference: str) -> Dict[str, Any]:
        # Operator naming: MTN, Airtel, 9mobile, Glo (Case Sensitive)
        network_map = {'mtn': 'MTN', 'glo': 'Glo', 'airtel': 'Airtel', '9mobile': '9mobile'}
        operator = network_map.get(network.lower(), 'MTN')

        payload = {
            "operator": operator,
            "type": "airtime",
            "value": int(amount),
            "phone": phone
        }
        
        res = self._post("topup", payload, reference)
        
        status = "FAILED"
        if res.get('status') == 'success':
            # transaction_status: 'completed', 'failed', or 'processing'
            txn_status = res.get('transaction_status', '').lower()
            if txn_status == 'completed':
                status = "SUCCESS"
            elif txn_status == 'processing':
                status = "PENDING"
            
        return {
            "status": status,
            "provider_reference": res.get('transaction_id', reference),
            "message": res.get('message'),
            "raw_response": res
        }

    def buy_data(self, phone: str, network: str, plan_id: str, amount: float, reference: str) -> Dict[str, Any]:
        network_map = {'mtn': 'MTN', 'glo': 'Glo', 'airtel': 'Airtel', '9mobile': '9mobile'}
        operator = network_map.get(network.lower(), 'MTN')

        payload = {
            "operator": operator,
            "type": "data",
            "value": plan_id, # Plan ID/Code from documentation tables
            "phone": phone
        }
        
        res = self._post("topup", payload, reference)
        
        status = "FAILED"
        if res.get('status') == 'success':
            txn_status = res.get('transaction_status', '').lower()
            if txn_status == 'completed':
                status = "SUCCESS"
            elif txn_status == 'processing':
                status = "PENDING"
        
        return {
            "status": status,
            "provider_reference": res.get('transaction_id', reference),
            "raw_response": res
        }

    def buy_tv(self, tv_id: str, package_id: str, smart_card_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Cable TV not supported by MobileVTU."}

    def buy_electricity(self, disco_id: str, plan_id: str, meter_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Electricity not supported by MobileVTU."}

    def buy_internet(self, plan_id: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Internet service not supported by MobileVTU."}

    def buy_education(self, exam_type: str, variation_id: str, quantity: int, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Education service not supported by MobileVTU."}

    def query_transaction(self, reference: str) -> Dict[str, Any]:
        payload = {"transaction_id": reference}
        res = self._post("transaction_status", payload)
        
        status = "UNKNOWN"
        if res.get('status') == 'success':
            txn_status = res.get('transaction_status') # ORDER_COMPLETED, ORDER_FAILED, etc.
            if txn_status == "ORDER_COMPLETED":
                status = "SUCCESS"
            elif txn_status == "ORDER_FAILED":
                status = "FAILED"
            else:
                status = "PENDING"
                
        return {
            "status": status,
            "raw_response": res
        }

    def cancel_transaction(self, reference: str) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Cancellation not supported by MobileVTU."}

    def handle_webhook(self, data: Dict[str, Any]) -> bool:
        # Documentation doesn't explicitly define webhook schema, 
        # but typical for this system is the query response format.
        return data.get("status") == "success"

    def handle_callback(self, data: Dict[str, Any]) -> bool:
        return self.handle_webhook(data)

    def validate_meter(self, meter_number: str, service: str) -> Dict[str, Any]:
        return {"account_name": "N/A", "raw_response": {}}

    def validate_cable_id(self, card_number: str, service: str) -> Dict[str, Any]:
        return {"account_name": "N/A", "raw_response": {}}

    def get_wallet_balance(self) -> float:
        res = self._post("check_balance", {"currency": "NGN"})
        try:
            # Response is typically {"data": [{"balance": "123"}]}
            return float(res.get('data', [{}])[0].get('balance', 0))
        except (IndexError, ValueError, TypeError):
            return 0.0

    def get_available_services(self) -> List[Dict[str, Any]]:
        return [
            {"type": "airtime", "endpoint": "topup"},
            {"type": "data", "endpoint": "fetch_data_plans"}
        ]

    def sync_airtime(self) -> int:
        from orders.models import AirtimeNetwork
        from summary.models import SiteConfig
        from decimal import Decimal
        config = SiteConfig.objects.first()
        margin = config.airtime_margin if config else Decimal('0.00')
        base_100 = Decimal('100.00')

        provider_config = getattr(self, "provider_config", None)
        networks = self.get_airtime_networks()
        created = []
        for net_data in networks:
            net, _ = AirtimeNetwork.objects.update_or_create(
                service_id=str(net_data.get("id")),
                provider=provider_config,
                defaults={
                    "service_name": net_data.get("name"),
                    "cost_price": base_100,
                    "selling_price": base_100 + margin,
                    "agent_price": base_100,
                }
            )
            created.append(net)
        return len(created)

    def sync_data(self) -> int:
        from orders.models import DataService, DataVariation
        from summary.models import SiteConfig
        from decimal import Decimal
        config = SiteConfig.objects.first()
        margin = config.data_margin if config else Decimal('0.00')

        provider_config = getattr(self, "provider_config", None)
        networks = self.get_airtime_networks()
        created_variations = []
        for net in networks:
            service, _ = DataService.objects.get_or_create(
                service_id=str(net["id"]),
                provider=provider_config,
                defaults={
                    "service_name": net["name"],
                }
            )
            plans = self.get_data_plans(net["id"])
            for plan in plans:
                p_amount = Decimal(str(plan.get("price") or 0))
                variation, _ = DataVariation.objects.update_or_create(
                    variation_id=str(plan.get("code") or plan.get("id")),
                    service=service,
                    defaults={
                        "name": plan.get("name"),
                        "cost_price": p_amount,
                        "selling_price": p_amount + margin,
                        "agent_price": p_amount,
                        "is_active": True,
                    }
                )
                created_variations.append(variation)
        return len(created_variations)

    def sync_cable(self) -> int:
        return 0

    def sync_electricity(self) -> int:
        return 0

    def sync_internet(self) -> int:
        return 0

    def sync_education(self) -> int:
        return 0

    def get_airtime_networks(self) -> List[Dict[str, Any]]:
        return [
            {"id": "MTN", "name": "MTN"},
            {"id": "Airtel", "name": "Airtel"},
            {"id": "Glo", "name": "Glo"},
            {"id": "9mobile", "name": "9mobile"}
        ]

    def get_data_plans(self, network_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetches plans directly from the API if network_id is provided.
        """
        if not network_id:
            return []
        
        # network_id must be case-sensitive (MTN, Airtel, etc.)
        res = self._post("fetch_data_plans", {"operator": network_id})
        return res.get('data', [])