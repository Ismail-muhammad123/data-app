import requests
import logging
from typing import Dict, Any, List, Optional
from ..interfaces import BaseVTUProvider

logger = logging.getLogger(__name__)

class MobileNigProvider(BaseVTUProvider):
    """
    MobileNig Enterprise implementation of BaseVTUProvider.
    Based on Postman Collection v2.1.
    """

    def __init__(self, config: Dict[str, Any]):
        self.public_key = config.get('public_key')
        self.secret_key = config.get('secret_key') # Required for Recharge/Renew
        self.base_url = config.get('base_url', 'https://enterprise.mobilenig.com/api/v2').rstrip('/')
        
        # Default headers for generic requests
        self.auth_headers = {
            "Authorization": f"Bearer {self.public_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Headers specifically for Recharge operations requiring secret key
        self.recharge_headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    @property
    def provider_name(self) -> str:
        return "mobilenig"

    @classmethod
    def get_supported_services(cls) -> List[str]:
        return ['airtime', 'data', 'tv', 'electricity', 'education']

    @classmethod
    def get_config_requirements(cls) -> List[Dict[str, Any]]:
        return [
            {'name': 'public_key', 'label': 'Public Key', 'type': 'text', 'required': True},
            {'name': 'secret_key', 'label': 'Secret Key', 'type': 'text', 'required': True},
            {'name': 'base_url', 'label': 'Base URL', 'type': 'text', 'required': False, 'default': 'https://enterprise.mobilenig.com/api/v2'}
        ]

    def _request(self, method: str, endpoint: str, data: dict = None, use_secret: bool = False) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = self.recharge_headers if use_secret else self.auth_headers
        try:
            response = requests.request(method, url, json=data, headers=headers, timeout=30)
            return response.json()
        except Exception as e:
            logger.error(f"MobileNig request error: {str(e)}")
            raise Exception(f"MobileNig API error: {str(e)}")

    def buy_airtime(self, phone: str, network: str, amount: float, reference: str) -> Dict[str, Any]:
        # Mapping based on collection: BAA (Airtel), BAB (Glo), BAC (9mobile), BAD (MTN)
        network_map = {'mtn': 'BAD', 'glo': 'BAB', '9mobile': 'BAC', 'airtel': 'BAA'}
        service_id = network_map.get(network.lower(), 'BAD')

        payload = {
            "service_id": service_id,
            "trans_id": reference[:15],  # MobileNig limit is 15 digits
            "service_type": "PREMIUM",   # Premium is discounted
            "phoneNumber": phone,
            "amount": int(amount)
        }
        
        res = self._request("POST", "/services/", payload, use_secret=True)
        
        status = "FAILED"
        # 200/201 is Success, 202 is Processing
        if str(res.get('statusCode')) in ['200', '201']:
            status = "SUCCESS"
        elif str(res.get('statusCode')) == '202':
            status = "PENDING"
            
        return {
            "status": status,
            "provider_reference": res.get('details', {}).get('trans_id', reference),
            "message": res.get('message'),
            "raw_response": res
        }

    def buy_data(self, phone: str, network: str, plan_id: str, amount: float, reference: str) -> Dict[str, Any]:
        # Mapping based on collection: BCA (MTN), BCB (9mobile), BCC (Glo), BCD (Airtel)
        network_map = {'mtn': 'BCA', '9mobile': 'BCB', 'glo': 'BCC', 'airtel': 'BCD'}
        service_id = network_map.get(network.lower(), 'BCA')

        payload = {
            "service_id": service_id,
            "service_type": "SME", # Common default, could be CORPORATE or GIFTING
            "beneficiary": phone,
            "trans_id": reference[:15],
            "code": plan_id,
            "amount": int(amount)
        }
        
        res = self._request("POST", "/services/", payload, use_secret=True)
        
        status = "FAILED"
        if str(res.get('statusCode')) in ['200', '201']:
            status = "SUCCESS"
        elif str(res.get('statusCode')) == '202':
            status = "PENDING"
            
        return {
            "status": status,
            "provider_reference": res.get('details', {}).get('trans_id', reference),
            "raw_response": res
        }

    def buy_tv(self, tv_id: str, package_id: str, smart_card_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        payload = {
            "service_id": tv_id, # e.g., 'AKA' for Gotv
            "trans_id": reference[:15],
            "amount": int(amount),
            "customerAccountId": smart_card_number
        }
        payload.update(kwargs)

        res = self._request("POST", "/services/", payload, use_secret=True)
        
        status = "SUCCESS" if str(res.get('statusCode')) in ['200', '201'] else "FAILED"
        return {
            "status": status,
            "provider_reference": res.get('details', {}).get('trans_id'),
            "raw_response": res
        }

    def buy_electricity(self, disco_id: str, plan_id: str, meter_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        payload = {
            "service_id": disco_id, # e.g., 'AMB' for Ikeja
            "trans_id": reference[:15],
            "amount": int(amount),
            "customerAccountId": meter_number
        }
        payload.update(kwargs)

        res = self._request("POST", "/services/", payload, use_secret=True)
        
        status = "SUCCESS" if str(res.get('statusCode')) in ['200', '201'] else "FAILED"
        return {
            "status": status,
            "provider_reference": res.get('details', {}).get('trans_id'),
            "raw_response": res
        }

    def buy_internet(self, plan_id: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Internet service not supported by MobileNig."}

    def buy_education(self, exam_type: str, variation_id: str, quantity: int, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        payload = {
            "service_id": exam_type, # e.g., 'AJA' for WAEC
            "trans_id": reference[:15],
            "amount": int(amount),
            "quantity": quantity
        }
        payload.update(kwargs)

        res = self._request("POST", "/services/", payload, use_secret=True)
        
        status = "SUCCESS" if str(res.get('statusCode')) in ['200', '201'] else "FAILED"
        return {
            "status": status,
            "provider_reference": res.get('details', {}).get('trans_id'),
            "raw_response": res
        }

    def query_transaction(self, reference: str) -> Dict[str, Any]:
        res = self._request("GET", f"/services/query?trans_id={reference}")
        status = "UNKNOWN"
        if res.get('details', {}).get('status') == 'Approved':
            status = "SUCCESS"
        elif res.get('details', {}).get('status') == 'Processing':
            status = "PENDING"
        return {"status": status, "raw_response": res}

    def cancel_transaction(self, reference: str) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Cancellation not supported by MobileNig."}

    def handle_webhook(self, data: Dict[str, Any]) -> bool:
        # Webhook format: {"username": "...", "status": "Approved", "trans_id": "...", "service_type": "..."}
        return data.get("status") == "Approved"

    def handle_callback(self, data: Dict[str, Any]) -> bool:
        return self.handle_webhook(data)

    def validate_meter(self, meter_number: str, service: str) -> Dict[str, Any]:
        payload = {"service_id": service, "customerAccountId": meter_number}
        res = self._request("POST", "/services/proxy", payload)
        details = res.get('details', {})
        return {
            "account_name": details.get('name') or details.get('customerName'),
            "raw_response": res
        }

    def validate_cable_id(self, card_number: str, service: str) -> Dict[str, Any]:
        payload = {"service_id": service, "customerAccountId": card_number}
        res = self._request("POST", "/services/proxy", payload)
        details = res.get('details', {})
        return {
            "account_name": f"{details.get('firstName', '')} {details.get('lastName', '')}".strip() or details.get('customerName'),
            "raw_response": res
        }

    def get_wallet_balance(self) -> float:
        res = self._request("GET", "/control/balance")
        return float(res.get('details', {}).get('balance', 0))

    def get_available_services(self) -> List[Dict[str, Any]]:
        res = self._request("GET", "/control/services_status?service_id=All")
        return res.get('details', [])

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
            {"id": "BAD", "name": "MTN"},
            {"id": "BAA", "name": "Airtel"},
            {"id": "BAB", "name": "Glo"},
            {"id": "BAC", "name": "9mobile"}
        ]

    def get_data_plans(self, network_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if not network_id: return []
        payload = {"service_id": network_id, "requestType": "SME"} # Default to SME
        res = self._request("POST", "/services/packages", payload)
        return res.get('details', [])

    def get_cable_tv_packages(self, service_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if not service_id: return []
        payload = {"service_id": service_id}
        res = self._request("POST", "/services/packages", payload)
        return res.get('details', [])

    def get_electricity_services(self) -> List[Dict[str, Any]]:
        # This filters the 'All Services' list for common electricity disco tags
        all_services = self.get_available_services()
        return [s for s in all_services if 'Prepaid' in s.get('name', '') or 'Postpaid' in s.get('name', '')]

    def get_internet_packages(self) -> List[Dict[str, Any]]:
        return []

    def get_education_services(self) -> List[Dict[str, Any]]:
        return [
            {"id": "AJA", "name": "WAEC"},
            {"id": "AJC", "name": "NECO"},
            {"id": "AJB", "name": "JAMB"}
        ]