import requests
import json
import logging
from typing import Dict, Any, Optional, List
from ..interfaces import BaseVTUProvider

logger = logging.getLogger(__name__)

class VTPassProvider(BaseVTUProvider):
    """
    VTPass implementation of BaseVTUProvider.
    """

    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get('api_key')
        self.public_key = config.get('public_key')
        self.secret_key = config.get('secret_key')
        self.base_url = config.get('base_url', 'https://vtpass.com/api')
        self.headers = {
            "api-key": self.api_key,
            "secret-key": self.secret_key,
            "Content-Type": "application/json",
        }

    @property
    def provider_name(self) -> str:
        return "vtpass"

    def _post(self, endpoint: str, payload: dict) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"VTPass request error: {str(e)}")
            raise Exception(f"VTPass API error: {str(e)}")

    def _get(self, endpoint: str) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"VTPass request error: {str(e)}")
            raise Exception(f"VTPass API error: {str(e)}")

    def buy_airtime(self, phone: str, network: str, amount: float, reference: str) -> Dict[str, Any]:
        payload = {
            "request_id": reference,
            "serviceID": network.lower(), # e.g. mtn, glo, airtel, mtn-airtime-prepaid
            "amount": float(amount),
            "phone": phone
        }
        res = self._post("/pay", payload)
        
        status = "PENDING"
        if res.get('code') == '000':
            status = "SUCCESS"
        elif res.get('code') in ['011', '012', '013', '014', '015', '016']:
            status = "FAILED"
            
        return {
            "status": status,
            "provider_reference": res.get('requestId'),
            "message": res.get('response_description'),
            "raw_response": res
        }

    def buy_data(self, phone: str, network: str, plan_id: str, amount: float, reference: str) -> Dict[str, Any]:
        payload = {
            "request_id": reference,
            "serviceID": network.lower(), # e.g. mtn-data, glo-data
            "billersCode": phone,
            "variation_code": plan_id,
            "amount": float(amount),
            "phone": phone
        }
        res = self._post("/pay", payload)
        
        status = "PENDING"
        if res.get('code') == '000':
            status = "SUCCESS"
        elif res.get('code') in ['011', '012', '013', '014', '015', '016']:
            status = "FAILED"
            
        return {
            "status": status,
            "provider_reference": res.get('requestId'),
            "message": res.get('response_description'),
            "raw_response": res
        }

    def pay_bill(self, service_type: str, identifier: str, amount: float, plan_id: str, reference: str, metadata: dict = None) -> Dict[str, Any]:
        payload = {
            "request_id": reference,
            "serviceID": service_type, # e.g. dstv, gotv, ikedc-postpaid
            "billersCode": identifier,
            "variation_code": plan_id,
            "amount": float(amount),
            "phone": metadata.get('phone') if metadata else identifier
        }
        res = self._post("/pay", payload)
        
        status = "PENDING"
        if res.get('code') == '000':
            status = "SUCCESS"
        elif res.get('code') in ['011', '012', '013', '014', '015', '016']:
            status = "FAILED"
            
        return {
            "status": status,
            "provider_reference": res.get('requestId'),
            "message": res.get('response_description'),
            "token": res.get('purchased_code'), # mostly for electricity
            "raw_response": res
        }

    def query_transaction(self, reference: str) -> Dict[str, Any]:
        res = self._post("/requery", {"request_id": reference})
        
        status = "PENDING"
        if res.get('code') == '000':
            status = "SUCCESS"
        elif res.get('code') in ['011', '012', '013', '014', '015', '016']:
            status = "FAILED"
            
        return {
            "status": status,
            "raw_response": res
        }

    def validate_meter(self, meter_number: str, service: str) -> Dict[str, Any]:
        payload = {
            "billersCode": meter_number,
            "serviceID": service,
            "type": "POSTPAID" if "postpaid" in service.lower() else "PREPAID"
        }
        res = self._post("/merchant-verify", payload)
        return {
            "account_name": res.get('content', {}).get('Customer_Name'),
            "raw_response": res
        }

    def validate_cable_id(self, card_number: str, service: str) -> Dict[str, Any]:
        payload = {
            "billersCode": card_number,
            "serviceID": service
        }
        res = self._post("/merchant-verify", payload)
        return {
            "account_name": res.get('content', {}).get('Customer_Name'),
            "raw_response": res
        }

    def get_wallet_balance(self) -> float:
        # VTPass doesn't have a direct "balance" API in the basic set, usually checked in dashboard
        # But some versions support it via POST /balance
        try:
            res = self._post("/balance", {})
            return float(res.get('contents', {}).get('balance', 0))
        except:
            return 0.0

    def get_available_services(self) -> List[Dict[str, Any]]:
        """
        Returns a list of available services from VTPass.
        """
        return [
            {"type": "airtime", "id": "mtn", "name": "MTN"},
            {"type": "airtime", "id": "glo", "name": "GLO"},
            {"type": "data", "id": "mtn-data", "name": "MTN Data"},
            {"type": "tv", "id": "dstv", "name": "DSTV"},
            {"type": "electricity", "id": "ikedc-postpaid", "name": "IKEDC Postpaid"},
        ]

    def get_airtime_networks(self) -> List[Dict[str, Any]]:
        res = self._get("/services?identifier=airtime")
        return res.get('content', [{}])[0].get('services', [])

    def get_data_plans(self, network_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if not network_id:
            return []
        res = self._get(f"/service-variations?serviceID={network_id}")
        return res.get('content', {}).get('varations', [])

    def get_cable_tv_packages(self, service_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if not service_id:
            return []
        res = self._get(f"/service-variations?serviceID={service_id}")
        return res.get('content', {}).get('varations', [])

    def get_electricity_services(self) -> List[Dict[str, Any]]:
        res = self._get("/services?identifier=electricity")
        return res.get('content', [{}])[0].get('services', [])

    def get_internet_packages(self) -> List[Dict[str, Any]]:
        res = self._get("/service-variations?serviceID=internet-direct")
        return res.get('content', {}).get('varations', [])

    def get_education_services(self) -> List[Dict[str, Any]]:
        res = self._get("/services?identifier=education")
        return res.get('content', [{}])[0].get('services', [])
