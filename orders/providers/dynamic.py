import requests
import logging
import json
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
        self.global_headers = config.get('global_headers', {})
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

    def _interpolate(self, value: Any, context: Dict[str, Any]) -> Any:
        if isinstance(value, str):
            for k, v in context.items():
                value = value.replace(f"{{{k}}}", str(v))
            return value
        elif isinstance(value, dict):
            return {k: self._interpolate(v, context) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._interpolate(v, context) for v in value]
        return value

    def _make_request(self, operation_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        op = self.operations.get(operation_type)
        if not op:
            logger.warning(f"Operation {operation_type} not configured for {self.provider_name}")
            return {"success": False, "error": f"Operation {operation_type} not configured"}

        context = data.copy()
        context['api_key'] = self.api_key
        # Ensure common aliases exist
        if 'phone' not in context and 'beneficiary' in context:
            context['phone'] = context['beneficiary']

        url = self._interpolate(f"{self.base_url.rstrip('/')}/{op['endpoint_path'].lstrip('/')}", context)
        
        # Build headers
        headers = self.global_headers.copy()
        if self.api_key_header and self.api_key:
            headers[self.api_key_header] = f"{self.api_key_prefix}{self.api_key}"
        
        op_headers = op.get('custom_headers', {})
        for k, v in op_headers.items():
            headers[k] = self._interpolate(v, context)
            
        # Build payload
        payload = op.get('static_params', {}).copy()
        for internal_key, provider_key in op.get('request_params', {}).items():
            if internal_key in data:
                payload[provider_key] = data[internal_key]
        
        custom_payload = op.get('custom_payload', {})
        for k, v in custom_payload.items():
            payload[k] = self._interpolate(v, context)

        method = op.get('method', 'POST').upper()
        
        try:
            if method == 'GET':
                response = requests.get(url, params=payload, headers=headers, timeout=30)
            elif method == 'POST':
                if self.request_format == 'json':
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
                else:
                    response = requests.post(url, data=payload, headers=headers, timeout=30)
            else:
                if self.request_format == 'json':
                    response = requests.request(method, url, json=payload, headers=headers, timeout=30)
                else:
                    response = requests.request(method, url, data=payload, headers=headers, timeout=30)
            
            resp_json = response.json()
            
            # Response Mapping
            success = False
            success_map = op.get('success_mapping', {})
            if success_map:
                success = True
                for k, v in success_map.items():
                    if k == 'http_code':
                        if response.status_code != int(v):
                            success = False; break
                    elif str(resp_json.get(k, '')).lower() != str(v).lower():
                        success = False; break
            else:
                success = (200 <= response.status_code < 300)

            # Data Extraction
            extracted = {}
            data_map = op.get('response_data_mapping', {})
            for our_key, their_key in data_map.items():
                val = resp_json
                for part in their_key.split('.'):
                    if isinstance(val, dict): val = val.get(part)
                    else: val = None; break
                extracted[our_key] = val

            return {
                "success": success,
                "response": resp_json,
                "status_code": response.status_code,
                "extracted": extracted
            }
        except Exception as e:
            logger.error(f"Dynamic Provider Request Error ({self.provider_name}): {e}")
            return {"success": False, "error": str(e)}

    def buy_airtime(self, phone: str, network: str, amount: float, reference: str) -> Dict[str, Any]:
        res = self._make_request('purchase', {
            'phone': phone, 'network': network, 'amount': amount, 'reference': reference, 'service_type': 'airtime'
        })
        extracted = res.get('extracted', {})
        return {
            "status": "SUCCESS" if res.get('success') else "FAILED", 
            "provider_reference": extracted.get('provider_reference', reference), 
            "message": extracted.get('message', ''),
            "raw_response": res.get('response')
        }

    def buy_data(self, phone: str, network: str, plan_id: str, amount: float, reference: str) -> Dict[str, Any]:
        res = self._make_request('purchase', {
            'phone': phone, 'network': network, 'plan_id': plan_id, 'amount': amount, 'reference': reference, 'service_type': 'data'
        })
        extracted = res.get('extracted', {})
        return {
            "status": "SUCCESS" if res.get('success') else "FAILED", 
            "provider_reference": extracted.get('provider_reference', reference), 
            "message": extracted.get('message', ''),
            "raw_response": res.get('response')
        }

    def buy_tv(self, tv_id: str, package_id: str, smart_card_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        res = self._make_request('purchase', {
            'tv_id': tv_id, 'package_id': package_id, 'smart_card_number': smart_card_number, 
            'phone': phone, 'amount': amount, 'reference': reference, 'service_type': 'tv', **kwargs
        })
        extracted = res.get('extracted', {})
        return {
            "status": "SUCCESS" if res.get('success') else "FAILED", 
            "provider_reference": extracted.get('provider_reference', reference), 
            "message": extracted.get('message', ''),
            "raw_response": res.get('response')
        }

    def buy_electricity(self, disco_id: str, plan_id: str, meter_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        res = self._make_request('purchase', {
            'disco_id': disco_id, 'plan_id': plan_id, 'meter_number': meter_number, 
            'phone': phone, 'amount': amount, 'reference': reference, 'service_type': 'electricity', **kwargs
        })
        extracted = res.get('extracted', {})
        return {
            "status": "SUCCESS" if res.get('success') else "FAILED", 
            "provider_reference": extracted.get('provider_reference', reference), 
            "token": extracted.get('token'),
            "message": extracted.get('message', ''),
            "raw_response": res.get('response')
        }

    def buy_internet(self, plan_id: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        res = self._make_request('purchase', {
            'plan_id': plan_id, 'phone': phone, 'amount': amount, 'reference': reference, 'service_type': 'internet', **kwargs
        })
        extracted = res.get('extracted', {})
        return {
            "status": "SUCCESS" if res.get('success') else "FAILED", 
            "provider_reference": extracted.get('provider_reference', reference), 
            "message": extracted.get('message', ''),
            "raw_response": res.get('response')
        }

    def buy_education(self, exam_type: str, variation_id: str, quantity: int, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        res = self._make_request('purchase', {
            'exam_type': exam_type, 'variation_id': variation_id, 'quantity': quantity, 
            'amount': amount, 'reference': reference, 'service_type': 'education', **kwargs
        })
        extracted = res.get('extracted', {})
        return {
            "status": "SUCCESS" if res.get('success') else "FAILED", 
            "provider_reference": extracted.get('provider_reference', reference), 
            "token": extracted.get('token'),
            "message": extracted.get('message', ''),
            "raw_response": res.get('response')
        }

    def query_transaction(self, reference: str) -> Dict[str, Any]:
        res = self._make_request('verify', {'reference': reference})
        extracted = res.get('extracted', {})
        return {
            "status": "SUCCESS" if res.get('success') else "FAILED", 
            "message": extracted.get('message', ''),
            "raw_response": res.get('response')
        }

    def cancel_transaction(self, reference: str) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Not supported"}

    def handle_webhook(self, data: Dict[str, Any]) -> bool:
        return False

    def handle_callback(self, data: Dict[str, Any]) -> bool:
        return False

    def validate_meter(self, meter_number: str, service: str) -> Dict[str, Any]:
        res = self._make_request('verify_customer', {'meter_number': meter_number, 'service_id': service})
        extracted = res.get('extracted', {})
        account_name = extracted.get('account_name')
        return {
            "status": "SUCCESS" if (res.get('success') and account_name) else "FAILED",
            "account_name": account_name,
            "raw_response": res.get('response', {})
        }

    def validate_cable_id(self, card_number: str, service: str) -> Dict[str, Any]:
        res = self._make_request('verify_customer', {'card_number': card_number, 'service_id': service})
        extracted = res.get('extracted', {})
        account_name = extracted.get('account_name')
        return {
            "status": "SUCCESS" if (res.get('success') and account_name) else "FAILED",
            "account_name": account_name,
            "raw_response": res.get('response', {})
        }

    def get_wallet_balance(self) -> float:
        res = self._make_request('balance', {})
        extracted = res.get('extracted', {})
        try:
            return float(extracted.get('balance', 0.0))
        except:
            return 0.0

    def get_available_services(self) -> List[Dict[str, Any]]:
        return []

    def sync_airtime(self) -> int: return 0
    def sync_data(self) -> int: return 0
    def sync_cable(self) -> int: return 0
    def sync_electricity(self) -> int: return 0
    def sync_internet(self) -> int: return 0
    def sync_education(self) -> int: return 0
