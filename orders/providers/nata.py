import requests
import logging
from typing import Dict, Any, List, Optional
from ..interfaces import BaseVTUProvider

logger = logging.getLogger(__name__)

class NataVTUProvider(BaseVTUProvider):
    """
    Nata.ng implementation of BaseVTUProvider.
    Documentation: https://api.nata.ng/merchant/api
    """

    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api.nata.ng/merchant/api').rstrip('/')
        
        # Nata's merchant API typically expects authentication headers
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    @property
    def provider_name(self) -> str:
        return "nata"

    @classmethod
    def get_supported_services(cls) -> List[str]:
        """
        Nata currently focuses on Airtime and Data for their merchant API.
        """
        return ['airtime', 'data']

    @classmethod
    def get_config_requirements(cls) -> List[Dict[str, Any]]:
        return [
            {'name': 'api_key', 'label': 'API Token', 'type': 'text', 'required': True},
            {'name': 'base_url', 'label': 'Base URL', 'type': 'text', 'required': False, 'default': 'https://api.nata.ng/merchant/api'}
        ]

    def _request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.request(method, url, json=data, params=params, headers=self.headers, timeout=30)
            return response.json()
        except Exception as e:
            logger.error(f"Nata request error: {str(e)}")
            raise Exception(f"Nata API error: {str(e)}")

    def buy_airtime(self, phone: str, network: str, amount: float, reference: str) -> Dict[str, Any]:
        """
        Initiate an airtime purchase.
        Network IDs: MTN=15, GLO=6, AIRTEL=1, 9MOBILE=2
        """
        network_map = {'mtn': 15, 'glo': 6, 'airtel': 1, '9mobile': 2}
        network_id = network_map.get(network.lower(), 15)

        payload = {
            "network": network_id,
            "amount": float(amount),
            "phone": phone,
            "reference": reference  # Unique Ref (6-12 chars)
        }
        
        res = self._request("POST", "buy-airtime", data=payload)
        
        # Nata returns 'status': 'success' for successfully initiated requests
        status = "FAILED"
        if res.get('status') == 'success':
            status = "SUCCESS" # Or "PENDING" if Nata processes asynchronously
            
        return {
            "status": status,
            "provider_reference": reference,
            "message": res.get('message'),
            "raw_response": res
        }

    def buy_data(self, phone: str, network: str, plan_id: str, amount: float, reference: str) -> Dict[str, Any]:
        """
        Initiate a data purchase.
        Requires plan_id and category (e.g., mtn_sme).
        """
        # Note: category is often part of the plan selection in VTU apps
        category = "mtn_sme" if "mtn" in network.lower() else network.lower()
        
        payload = {
            "plan_id": int(plan_id),
            "category": category,
            "phone": phone,
            "reference": reference
        }
        
        res = self._request("POST", "buy-data", data=payload)
        
        status = "SUCCESS" if res.get('status') == 'success' else "FAILED"
        
        return {
            "status": status,
            "provider_reference": reference,
            "message": res.get('message'),
            "raw_response": res
        }

    def buy_tv(self, tv_id: str, package_id: str, smart_card_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Cable TV not supported by Nata."}

    def buy_electricity(self, disco_id: str, plan_id: str, meter_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Electricity not supported by Nata."}

    def buy_internet(self, plan_id: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Internet service not supported by Nata."}

    def buy_education(self, exam_type: str, variation_id: str, quantity: int, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Education service not supported by Nata."}

    def query_transaction(self, reference: str) -> Dict[str, Any]:
        """
        Check status of a transaction using your reference.
        """
        res = self._request("GET", f"transactions/{reference}")
        status = "UNKNOWN"
        if res.get('success'):
            data = res.get('data', {})
            txn_status = data.get('status', '').lower()
            if txn_status == 'successful':
                status = "SUCCESS"
            elif txn_status == 'failed':
                status = "FAILED"
            else:
                status = "PENDING"
        return {"status": status, "raw_response": res}

    def cancel_transaction(self, reference: str) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Cancellation not supported by Nata."}

    def handle_webhook(self, data: Dict[str, Any]) -> bool:
        return data.get('status') == 'success'

    def handle_callback(self, data: Dict[str, Any]) -> bool:
        return self.handle_webhook(data)

    def validate_meter(self, meter_number: str, service: str) -> Dict[str, Any]:
        return {"account_name": "N/A", "raw_response": {}}

    def validate_cable_id(self, card_number: str, service: str) -> Dict[str, Any]:
        return {"account_name": "N/A", "raw_response": {}}

    def get_wallet_balance(self) -> float:
        res = self._request("GET", "user")
        return float(res.get('data', {}).get('balance', 0))

    def get_available_services(self) -> List[Dict[str, Any]]:
        return [
            {"type": "airtime", "endpoint": "airtime"},
            {"type": "data", "endpoint": "data-plans"}
        ]

    def sync_airtime(self) -> int:
        from orders.models import AirtimeNetwork
        from summary.models import SiteConfig
        from decimal import Decimal
        config = SiteConfig.objects.first()
        margin = config.airtime_margin if config else Decimal('0.00')
        base_100 = Decimal('100.00')

        networks = self.get_airtime_networks()
        created = []
        for net_data in networks:
            net, _ = AirtimeNetwork.objects.update_or_create(
                service_id=str(net_data.get("id")),
                defaults={
                    "service_name": net_data.get("name"),
                    "cost_price": base_100,
                    "selling_price": base_100 + margin,
                    "agent_price": base_100,
                    "provider": getattr(self, "provider_config", None),
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

        plans = self.get_data_plans()
        created_variations = []
        for plan in plans:
            service, _ = DataService.objects.get_or_create(
                service_id=plan.get("category", "general"),
                defaults={
                    "service_name": plan.get("category", "General").replace("_", " ").title(),
                    "provider": getattr(self, "provider_config", None),
                }
            )
            p_amount = Decimal(str(plan.get("price", 0)))
            variation, _ = DataVariation.objects.update_or_create(
                variation_id=str(plan.get("id")),
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
        res = self._request("GET", "airtime")
        return res.get('data', [])

    def get_data_plans(self, network_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetches plans from /data-plans.
        """
        params = {"category": network_id} if network_id else {}
        res = self._request("GET", "data-plans", params=params)
        return res.get('data', [])