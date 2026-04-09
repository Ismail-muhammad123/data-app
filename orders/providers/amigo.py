import requests
import logging
import uuid
from typing import Dict, Any, List, Optional
from ..interfaces import BaseVTUProvider

logger = logging.getLogger(__name__)

class AmigoVTUProvider(BaseVTUProvider):
    """
    Amigo.ng implementation of BaseVTUProvider.
    Documentation: https://amigo.ng/amigo-api-docs.html
    """

    def __init__(self, config: Dict[str, Any]):
        self.api_token = config.get('api_key')
        self.base_url = config.get('base_url', 'https://amigo.ng/api').rstrip('/')
        
        self.headers = {
            "X-API-Key": self.api_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    @property
    def provider_name(self) -> str:
        return "amigo"

    @classmethod
    def get_supported_services(cls) -> List[str]:
        """
        Amigo supports Airtime and Data (MTN, Glo, and Airtel).
        """
        return ['airtime', 'data']

    @classmethod
    def get_config_requirements(cls) -> List[Dict[str, Any]]:
        return [
            {'name': 'api_key', 'label': 'API Token', 'type': 'text', 'required': True},
            {'name': 'base_url', 'label': 'Base URL', 'type': 'text', 'required': False, 'default': 'https://amigo.ng/api'}
        ]

    def _post(self, endpoint: str, data: dict, idempotency_key: str = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self.headers.copy()
        
        # Add idempotency key to prevent double charging on retries
        headers["Idempotency-Key"] = idempotency_key or str(uuid.uuid4())
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            return response.json()
        except Exception as e:
            logger.error(f"Amigo request error: {str(e)}")
            raise Exception(f"Amigo API error: {str(e)}")

    def buy_airtime(self, phone: str, network: str, amount: float, reference: str) -> Dict[str, Any]:
        """
        Purchase airtime. 
        Network IDs: MTN=1, Glo=2, Airtel=4.
        """
        network_map = {'mtn': 1, 'glo': 2, 'airtel': 4}
        network_id = network_map.get(network.lower(), 1)

        payload = {
            "network": network_id,
            "mobile_number": phone,
            "amount": int(amount),
            "airtime_type": "VTU"
        }
        
        # Airtime endpoint is typically /airtime/ on this platform
        res = self._post("airtime/", payload, idempotency_key=reference)
        
        status = "FAILED"
        if res.get('success') is True:
            status = "SUCCESS"
        elif res.get('status') == 'processing':
            status = "PENDING"
            
        return {
            "status": status,
            "provider_reference": res.get('reference', reference),
            "message": res.get('message'),
            "raw_response": res
        }

    def buy_data(self, phone: str, network: str, plan_id: str, amount: float, reference: str) -> Dict[str, Any]:
        """
        Purchase a data plan.
        Plan IDs are integers (e.g., 1001 for 1GB).
        """
        network_map = {'mtn': 1, 'glo': 2, 'airtel': 4}
        network_id = network_map.get(network.lower(), 1)

        payload = {
            "network": network_id,
            "mobile_number": phone,
            "plan": int(plan_id),
            "Ported_number": True
        }
        
        res = self._post("data/", payload, idempotency_key=reference)
        
        status = "FAILED"
        if res.get('success') is True:
            # Amigo returns status 'delivered' for successful data gifts
            if res.get('status') == 'delivered':
                status = "SUCCESS"
            else:
                status = "PENDING"
        
        return {
            "status": status,
            "provider_reference": res.get('reference', reference),
            "message": res.get('message'),
            "raw_response": res
        }

    def buy_tv(self, tv_id: str, package_id: str, smart_card_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Cable TV not supported by Amigo."}

    def buy_electricity(self, disco_id: str, plan_id: str, meter_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Electricity not supported by Amigo."}

    def buy_internet(self, plan_id: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Internet service not supported by Amigo."}

    def buy_education(self, exam_type: str, variation_id: str, quantity: int, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Education service not supported by Amigo."}

    def query_transaction(self, reference: str) -> Dict[str, Any]:
        """
        Amigo usually allows fetching transaction details by reference via GET.
        """
        url = f"{self.base_url}/user/transactions/{reference}"
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            res = response.json()
            status = "UNKNOWN"
            if res.get('success'):
                status = "SUCCESS" if res.get('status') == 'delivered' else "PENDING"
            return {"status": status, "raw_response": res}
        except:
            return {"status": "FAILED", "raw_response": {}}

    def cancel_transaction(self, reference: str) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Cancellation not supported by Amigo."}

    def handle_webhook(self, data: Dict[str, Any]) -> bool:
        return data.get('success') is True and data.get('status') == 'delivered'

    def handle_callback(self, data: Dict[str, Any]) -> bool:
        return self.handle_webhook(data)

    def validate_meter(self, meter_number: str, service: str) -> Dict[str, Any]:
        return {"account_name": "N/A", "raw_response": {}}

    def validate_cable_id(self, card_number: str, service: str) -> Dict[str, Any]:
        return {"account_name": "N/A", "raw_response": {}}

    def get_wallet_balance(self) -> float:
        """
        Fetch balance from the user endpoint.
        """
        try:
            url = f"{self.base_url}/user/"
            response = requests.get(url, headers=self.headers, timeout=30)
            res = response.json()
            return float(res.get('user', {}).get('balance', 0))
        except:
            return 0.0

    def get_available_services(self) -> List[Dict[str, Any]]:
        return [
            {"type": "airtime", "networks": ["MTN", "Glo", "Airtel"]},
            {"type": "data", "networks": ["MTN", "Glo", "Airtel"]}
        ]

    def sync_airtime(self) -> int:
        return 0

    def sync_data(self) -> int:
        return 0

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
            {"id": 1, "name": "MTN"},
            {"id": 2, "name": "Glo"},
            {"id": 4, "name": "Airtel"}
        ]

    def get_data_plans(self, network_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Hardcoded plan catalog from Amigo documentation.
        """
        all_plans = [
            {"id": "1001", "name": "1GB", "network": "1", "price": 429},
            {"id": "6666", "name": "2GB", "network": "1", "price": 849},
            {"id": "9999", "name": "5GB", "network": "1", "price": 1799},
            {"id": "5000", "name": "500MB", "network": "2", "price": 299},
        ]
        if network_id:
            return [p for p in all_plans if p['network'] == str(network_id)]
        return all_plans