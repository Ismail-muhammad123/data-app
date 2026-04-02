import requests
import json
import logging
from typing import Dict, Any, List, Optional
from ..interfaces import BaseVTUProvider

logger = logging.getLogger(__name__)

class GenericLocalProvider(BaseVTUProvider):
    """
    Standard implementation for many Nigerian VTU APIs (Alrahuz, MobileNIG, etc.) 
    that share similar request/response structures.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url')

    @property
    def provider_name(self) -> str:
        return self.config.get('name', 'generic')

    def _get_headers(self):
        return {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
        }

    def buy_airtime(self, phone: str, network: str, amount: float, reference: str) -> Dict[str, Any]:
        payload = {
            "network": network, # Expected to be the numeric ID or string required by specific generic API
            "amount": int(amount),
            "mobile_number": phone,
            "Ported_number": True,
            "airtime_type": "VTU"
        }
        url = f"{self.base_url}/topup/"
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=20)
            data = response.json()
            if data.get('Status') == 'successful':
                return {"status": "SUCCESS", "provider_reference": data.get('id'), "raw_response": data}
            return {"status": "FAILED", "message": data.get('error', 'Transaction failed'), "raw_response": data}
        except Exception as e:
            return {"status": "FAILED", "message": str(e)}

    def buy_data(self, phone: str, network: str, plan_id: str, amount: float, reference: str) -> Dict[str, Any]:
        payload = {
            "network": network,
            "mobile_number": phone,
            "plan": plan_id,
            "Ported_number": True
        }
        url = f"{self.base_url}/data/"
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=20)
            data = response.json()
            if data.get('Status') == 'successful':
                return {"status": "SUCCESS", "provider_reference": data.get('id'), "raw_response": data}
            return {"status": "FAILED", "message": data.get('error', 'Transaction failed'), "raw_response": data}
        except Exception as e:
            return {"status": "FAILED", "message": str(e)}

    def pay_bill(self, service_type: str, identifier: str, amount: float, plan_id: str, reference: str, metadata: dict = None) -> Dict[str, Any]:
        # Implementation depends on whether it's TV, Electricity or Education
        # Generic APIs usually separate these. We'll branch based on service_type or identifier hints.
        if any(x in service_type.lower() for x in ['dstv', 'gotv', 'startimes']):
            # TV
            payload = {
                "cablename": service_type,
                "smart_card_number": identifier,
                "cableplan": plan_id,
            }
            url = f"{self.base_url}/cablesub/"
        else:
            # Electricity
            payload = {
                "disco_name": service_type,
                "meter_number": identifier,
                "Meter_Type": "Prepaid",
                "amount": int(amount),
            }
            url = f"{self.base_url}/billpayment/"

        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=20)
            data = response.json()
            if data.get('Status') == 'successful':
                return {"status": "SUCCESS", "token": data.get('main_token'), "raw_response": data}
            return {"status": "FAILED", "message": data.get('error', 'Transaction failed'), "raw_response": data}
        except Exception as e:
            return {"status": "FAILED", "message": str(e)}

    def query_transaction(self, reference: str) -> Dict[str, Any]:
        url = f"{self.base_url}/query-status/{reference}/"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=15)
            data = response.json()
            status = "SUCCESS" if data.get('Status') == 'successful' else "FAILED"
            return {"status": status, "raw_response": data}
        except:
            return {"status": "PENDING", "error": "Query failed"}

    def validate_meter(self, meter_number: str, service: str) -> Dict[str, Any]:
        url = f"{self.base_url}/validate_meter/?meternumber={meter_number}&disconame={service}&mtype=Prepaid"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=15)
            data = response.json()
            return {"account_name": data.get('name'), "raw_response": data}
        except:
            return {"error": "Verification failed"}

    def validate_cable_id(self, card_number: str, service: str) -> Dict[str, Any]:
        url = f"{self.base_url}/validate_iuc/?smart_card_number={card_number}&cablename={service}"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=15)
            data = response.json()
            return {"account_name": data.get('name'), "raw_response": data}
        except:
            return {"error": "Verification failed"}

    def get_wallet_balance(self) -> float:
        try:
            url = f"{self.base_url}/user/"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            return float(response.json().get('user', {}).get('balance', 0))
        except:
            return 0.0

    def get_available_services(self) -> List[Dict[str, Any]]:
        return [
            {"type": "airtime", "id": "1", "name": "MTN"},
            {"type": "data", "id": "1", "name": "MTN Data"},
        ]

    def get_airtime_networks(self) -> List[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/networks/"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            return response.json()
        except: return []

    def get_data_plans(self, network_id: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/dataplans/?network={network_id}" if network_id else f"{self.base_url}/dataplans/"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            return response.json()
        except: return []

    def get_cable_tv_packages(self, service_id: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/cableplans/?cablename={service_id}" if service_id else f"{self.base_url}/cableplans/"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            return response.json()
        except: return []

    def get_electricity_services(self) -> List[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/discos/"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            return response.json()
        except: return []

    def get_internet_packages(self) -> List[Dict[str, Any]]:
        return []

    def get_education_services(self) -> List[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/education/"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            return response.json()
        except: return []
