import requests
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class AlrahuzDataProvider(BaseVTUProvider):
    """
    Alrahuz Data implementation of BaseVTUProvider.
    Documentation: https://documenter.getpostman.com/view/18957639/2s9YR6buRK
    """

    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://alrahuzdata.com.ng').rstrip('/')
        
        self.headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
        }

    @property
    def provider_name(self) -> str:
        return "alrahuz"

    @classmethod
    def get_supported_services(cls) -> List[str]:
        return ['airtime', 'data', 'tv', 'electricity']

    @classmethod
    def get_config_requirements(cls) -> List[Dict[str, Any]]:
        return [
            {'name': 'api_key', 'label': 'API Token', 'type': 'text', 'required': True},
            {'name': 'base_url', 'label': 'Base URL', 'type': 'text', 'required': False, 'default': 'https://alrahuzdata.com.ng'}
        ]

    def _request(self, method: str, endpoint: str, data: dict = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, json=data, headers=self.headers, timeout=30)
            return response.json()
        except Exception as e:
            logger.error(f"Alrahuz request error: {str(e)}")
            raise Exception(f"Alrahuz API error: {str(e)}")

    def buy_airtime(self, phone: str, network: str, amount: float, reference: str) -> Dict[str, Any]:
        network_map = {'mtn': 1, 'glo': 2, '9mobile': 3, 'airtel': 4}
        
        payload = {
            "network": network_map.get(network.lower(), 1),
            "amount": int(amount),
            "mobile_number": phone,
            "Ported_number": True,
            "airtime_type": "VTU"
        }
        
        res = self._request("POST", "/api/airtime/", payload)
        
        status = "FAILED"
        if res.get('Status') == 'success':
            status = "SUCCESS"
        elif res.get('Status') == 'processing':
            status = "PENDING"
            
        return {
            "status": status,
            "provider_reference": res.get('id', reference),
            "raw_response": res
        }

    def buy_data(self, phone: str, network: str, plan_id: str, amount: float, reference: str) -> Dict[str, Any]:
        network_map = {'mtn': 1, 'glo': 2, '9mobile': 3, 'airtel': 4}
        
        payload = {
            "network": network_map.get(network.lower(), 1),
            "mobile_number": phone,
            "plan": plan_id,
            "Ported_number": True
        }
        
        res = self._request("POST", "/api/data/", payload)
        
        status = "FAILED"
        if res.get('Status') == 'success':
            status = "SUCCESS"
        
        return {
            "status": status,
            "provider_reference": res.get('id', reference),
            "raw_response": res
        }

    def pay_bill(self, service_type: str, identifier: str, amount: float, plan_id: str, reference: str, metadata: dict = None) -> Dict[str, Any]:
        if service_type.lower() in ['dstv', 'gotv', 'startimes']:
            cable_map = {'gotv': 1, 'dstv': 2, 'startimes': 3}
            payload = {
                "cablename": cable_map.get(service_type.lower()),
                "cableplan": plan_id,
                "smart_card_number": identifier
            }
            endpoint = "/api/cablesub/"
        else:
            # Electricity
            payload = {
                "disco_name": service_type, # Use Disco ID
                "amount": int(amount),
                "meter_number": identifier,
                "Meter_Type": metadata.get('meter_type', 'Prepaid')
            }
            endpoint = "/api/billpayment/"

        res = self._request("POST", endpoint, payload)
        status = "SUCCESS" if res.get('Status') == 'success' else "FAILED"
        
        return {
            "status": status,
            "provider_reference": res.get('id'),
            "raw_response": res
        }

    def query_transaction(self, reference: str) -> Dict[str, Any]:
        # Documentation specifies querying by the ID returned during creation
        res = self._request("GET", f"/api/data/{reference}")
        return {"status": "SUCCESS" if res.get('Status') == 'success' else "FAILED", "raw_response": res}

    def handle_webhook(self, data: Dict[str, Any]) -> bool:
        return data.get('status') == 'success'

    def handle_callback(self, data: Dict[str, Any]) -> bool:
        return self.handle_webhook(data)

    def validate_meter(self, meter_number: str, service: str) -> Dict[str, Any]:
        res = self._request("GET", f"/api/validator/meter/?meter_number={meter_number}&disco={service}")
        return {"account_name": res.get('name'), "raw_response": res}

    def validate_cable_id(self, card_number: str, service: str) -> Dict[str, Any]:
        res = self._request("GET", f"/api/validator/cable/?smart_card_number={card_number}&cablename={service}")
        return {"account_name": res.get('name'), "raw_response": res}

    def get_wallet_balance(self) -> float:
        res = self._request("GET", "/api/user/")
        return float(res.get('user', {}).get('balance', 0))

    def get_available_services(self) -> List[Dict[str, Any]]:
        return [
            {"type": "airtime", "networks": self.get_airtime_networks()},
            {"type": "data", "plans": self.get_data_plans()},
            {"type": "tv", "cables": self.get_cable_tv_packages()},
            {"type": "electricity", "discos": self.get_electricity_services()}
        ]

    def get_airtime_networks(self) -> List[Dict[str, Any]]:
        return [
            {"id": 1, "name": "MTN"},
            {"id": 2, "name": "GLO"},
            {"id": 3, "name": "9MOBILE"},
            {"id": 4, "name": "AIRTEL"}
        ]

    def get_data_plans(self, network_id: Optional[str] = None) -> List[Dict[str, Any]]:
        # Hardcoded from HTML table provided
        all_plans = [
            {"id": "7", "network": "MTN", "name": "SME 1.0GB", "amount": 780},
            {"id": "8", "network": "MTN", "name": "SME 2.0GB", "amount": 1450},
            {"id": "285", "network": "GLO", "name": "CG 1.0GB", "amount": 400},
            {"id": "516", "network": "AIRTEL", "name": "CG 1.0GB", "amount": 784},
            {"id": "248", "network": "9MOBILE", "name": "SME 1.0GB", "amount": 220},
        ]
        if network_id:
            return [p for p in all_plans if p['network'] == network_id]
        return all_plans

    def get_cable_tv_packages(self, service_id: Optional[str] = None) -> List[Dict[str, Any]]:
        # Hardcoded from HTML table provided
        all_packages = [
            {"id": "2", "cable": "GOTV", "name": "GOtv Max", "amount": 8500},
            {"id": "6", "cable": "DSTV", "name": "DStv Yanga", "amount": 6000},
            {"id": "12", "cable": "STARTIME", "name": "Basic", "amount": 4000},
        ]
        if service_id:
            return [p for p in all_packages if p['cable'] == service_id]
        return all_packages

    def get_electricity_services(self) -> List[Dict[str, Any]]:
        return [
            {"id": 1, "name": "Ikeja Electric"},
            {"id": 2, "name": "Eko Electric"},
            {"id": 3, "name": "Abuja Electric"},
            {"id": 7, "name": "Ibadan Electric"}
        ]

    def get_internet_packages(self) -> List[Dict[str, Any]]:
        return []

    def get_education_services(self) -> List[Dict[str, Any]]:
        return []