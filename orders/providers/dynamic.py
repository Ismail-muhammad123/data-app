import requests
import logging
from typing import Dict, Any, List, Optional
from ..interfaces import BaseVTUProvider

logger = logging.getLogger(__name__)

class DynamicProvider(BaseVTUProvider):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._name = config.get('name', 'dynamic')
        self.base_url = config.get('base_url', '')
        self.api_key = config.get('api_key', '')
        self.api_key_header = config.get('api_key_header', 'Authorization')
        self.api_key_prefix = config.get('api_key_prefix', 'Token ')
        self.request_format = config.get('request_format', 'json')
        
        # Operations mapping from config
        self.operations = config.get('operations', {})

    @property
    def provider_name(self) -> str:
        return self._name

    @classmethod
    def get_supported_services(cls) -> List[str]:
        return ['airtime', 'data', 'tv', 'electricity', 'internet', 'education']

    @classmethod
    def get_config_requirements(cls) -> List[Dict[str, Any]]:
        return []

    def _make_request(self, operation_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        op = self.operations.get(operation_type)
        if not op:
            logger.warning(f"Operation {operation_type} not configured for {self.provider_name}")
            return {"success": False, "error": "Operation not configured"}

        url = f"{self.base_url.rstrip('/')}/{op['endpoint_path'].lstrip('/')}"
        headers = {
            self.api_key_header: f"{self.api_key_prefix}{self.api_key}"
        }
        
        payload = op.get('static_params', {}).copy()
        for internal_key, provider_key in op.get('request_params', {}).items():
            if internal_key in data:
                payload[provider_key] = data[internal_key]

        try:
            if op['method'] == 'GET':
                response = requests.get(url, params=payload, headers=headers, timeout=30)
            else:
                if self.request_format == 'json':
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
                else:
                    response = requests.post(url, data=payload, headers=headers, timeout=30)
            
            resp_json = response.json()
            
            success = False
            cond = op.get('success_condition', {})
            if cond and 'field' in cond and 'value' in cond:
                field_val = str(resp_json.get(cond['field'])).lower()
                expected_val = str(cond['value']).lower()
                if field_val == expected_val:
                    success = True
            
            return {
                "success": success,
                "response": resp_json,
                "status_code": response.status_code
            }
        except Exception as e:
            logger.error(f"Dynamic Provider Request Error ({self.provider_name}): {e}")
            return {"success": False, "error": str(e)}

    def buy_airtime(self, phone: str, network: str, amount: float, reference: str) -> Dict[str, Any]:
        res = self._make_request('purchase', {
            'phone': phone, 'network': network, 'amount': amount, 'reference': reference, 'service_type': 'airtime'
        })
        return {"status": "SUCCESS" if res.get('success') else "FAILED", "provider_reference": reference, "raw_response": res.get('response')}

    def buy_data(self, phone: str, network: str, plan_id: str, amount: float, reference: str) -> Dict[str, Any]:
        res = self._make_request('purchase', {
            'phone': phone, 'network': network, 'plan_id': plan_id, 'amount': amount, 'reference': reference, 'service_type': 'data'
        })
        return {"status": "SUCCESS" if res.get('success') else "FAILED", "provider_reference": reference, "raw_response": res.get('response')}

    def buy_tv(self, tv_id: str, package_id: str, smart_card_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        res = self._make_request('purchase', {
            'tv_id': tv_id, 'package_id': package_id, 'smart_card_number': smart_card_number, 
            'phone': phone, 'amount': amount, 'reference': reference, 'service_type': 'tv', **kwargs
        })
        return {"status": "SUCCESS" if res.get('success') else "FAILED", "provider_reference": reference, "raw_response": res.get('response')}

    def buy_electricity(self, disco_id: str, plan_id: str, meter_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        res = self._make_request('purchase', {
            'disco_id': disco_id, 'plan_id': plan_id, 'meter_number': meter_number, 
            'phone': phone, 'amount': amount, 'reference': reference, 'service_type': 'electricity', **kwargs
        })
        return {"status": "SUCCESS" if res.get('success') else "FAILED", "provider_reference": reference, "raw_response": res.get('response')}

    def buy_internet(self, plan_id: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        res = self._make_request('purchase', {
            'plan_id': plan_id, 'phone': phone, 'amount': amount, 'reference': reference, 'service_type': 'internet', **kwargs
        })
        return {"status": "SUCCESS" if res.get('success') else "FAILED", "provider_reference": reference, "raw_response": res.get('response')}

    def buy_education(self, exam_type: str, variation_id: str, quantity: int, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        res = self._make_request('purchase', {
            'exam_type': exam_type, 'variation_id': variation_id, 'quantity': quantity, 
            'amount': amount, 'reference': reference, 'service_type': 'education', **kwargs
        })
        return {"status": "SUCCESS" if res.get('success') else "FAILED", "provider_reference": reference, "raw_response": res.get('response')}

    def query_transaction(self, reference: str) -> Dict[str, Any]:
        res = self._make_request('verify', {'reference': reference})
        return {"status": "SUCCESS" if res.get('success') else "FAILED", "raw_response": res.get('response')}

    def cancel_transaction(self, reference: str) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Not supported"}

    def handle_webhook(self, data: Dict[str, Any]) -> bool:
        return False

    def handle_callback(self, data: Dict[str, Any]) -> bool:
        return False

    def validate_meter(self, meter_number: str, service: str) -> Dict[str, Any]:
        res = self._make_request('verify_customer', {'meter_number': meter_number, 'service_id': service})
        return res.get('response', {})

    def validate_cable_id(self, card_number: str, service: str) -> Dict[str, Any]:
        res = self._make_request('verify_customer', {'card_number': card_number, 'service_id': service})
        return res.get('response', {})

    def get_wallet_balance(self) -> float:
        return 0.0

    def get_available_services(self) -> List[Dict[str, Any]]:
        return []

    def sync_airtime(self) -> int: return 0
    def sync_data(self) -> int: return 0
    def sync_cable(self) -> int: return 0
    def sync_electricity(self) -> int: return 0
    def sync_internet(self) -> int: return 0
    def sync_education(self) -> int: return 0
