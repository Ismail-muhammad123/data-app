import requests
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class SMEDataProvider(BaseVTUProvider):
    """
    SMEData.ng implementation of BaseVTUProvider.
    Documentation: https://smedata.ng/mtn-sme-data-api-documentation-for-developers/
    """

    def __init__(self, config: Dict[str, Any]):
        self.token = config.get('api_key')  # SMEData calls it 'token'
        self.base_url = config.get('base_url', 'https://smedata.ng/wp-json/api/v1').rstrip('/')

    @property
    def provider_name(self) -> str:
        return "smedata"

    @classmethod
    def get_supported_services(cls) -> List[str]:
        """
        SMEData specializes in Data and Requery services via the provided documentation.
        """
        return ['data']

    @classmethod
    def get_config_requirements(cls) -> List[Dict[str, Any]]:
        return [
            {
                'name': 'api_key', 
                'label': 'API Token', 
                'type': 'text', 
                'required': True,
                'help_text': 'Unique API Token generated in the Reseller Dashboard'
            },
            {
                'name': 'base_url', 
                'label': 'Base URL', 
                'type': 'text', 
                'required': False, 
                'default': 'https://smedata.ng/wp-json/api/v1'
            }
        ]

    def _get(self, endpoint: str, params: dict) -> Dict[str, Any]:
        """
        SMEData uses HTTP GET for all requests.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        params.update({"token": self.token})
        try:
            response = requests.get(url, params=params, timeout=30)
            return response.json()
        except Exception as e:
            logger.error(f"SMEData request error: {str(e)}")
            raise Exception(f"SMEData API error: {str(e)}")

    def buy_airtime(self, phone: str, network: str, amount: float, reference: str) -> Dict[str, Any]:
        """
        Airtime implementation is not explicitly detailed in the provided snippet, 
        though common on these platforms. 
        """
        return {"status": "FAILED", "message": "Airtime service not detailed in current documentation."}

    def buy_data(self, phone: str, network: str, plan_id: str, amount: float, reference: str) -> Dict[str, Any]:
        """
        Purchase Data using GET request.
        Endpoint: /data
        """
        # SMEData expects lowercase networks: mtn, glo, airtel
        params = {
            "network": network.lower(),
            "phone": phone,
            "size": plan_id  # e.g., '1gb', '500mb'
        }
        
        res = self._get("data", params)
        
        status = "PENDING"
        code = res.get('code', '').lower()
        
        if code == 'success':
            status = "SUCCESS"
        elif code == 'failure':
            status = "FAILED"
            
        return {
            "status": status,
            "provider_reference": res.get('data', {}).get('order_id'),
            "message": res.get('message'),
            "raw_response": res
        }

    def pay_bill(self, service_type: str, identifier: str, amount: float, plan_id: str, reference: str, metadata: dict = None) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Bill payment service not detailed in documentation."}

    def query_transaction(self, reference: str) -> Dict[str, Any]:
        """
        Requery a transaction status.
        Endpoint: /requery
        """
        params = {"orderid": reference}
        res = self._get("requery", params)
        
        code = res.get('code', '').lower()
        status = "PENDING"
        
        if code == "success":
            status = "SUCCESS"
        elif code == "failure":
            status = "FAILED"
        elif code == "processing":
            status = "PENDING"
            
        return {
            "status": status,
            "raw_response": res
        }

    def handle_webhook(self, data: Dict[str, Any]) -> bool:
        """
        Processes SMEData webhook.
        Expects keys: code (success/failure), data -> order_id
        """
        code = data.get("code", "").lower()
        return code == "success"

    def handle_callback(self, data: Dict[str, Any]) -> bool:
        return self.handle_webhook(data)

    def validate_meter(self, meter_number: str, service: str) -> Dict[str, Any]:
        return {"account_name": "N/A", "raw_response": {}}

    def validate_cable_id(self, card_number: str, service: str) -> Dict[str, Any]:
        return {"account_name": "N/A", "raw_response": {}}

    def get_wallet_balance(self) -> float:
        """
        Documentation does not provide a balance endpoint, 
        usually handled via account/user endpoints.
        """
        return 0.0

    def get_available_services(self) -> List[Dict[str, Any]]:
        return [{"type": "data"}]

    def get_airtime_networks(self) -> List[Dict[str, Any]]:
        return []

    def get_data_plans(self, network_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Hardcoded Data Plan IDs/Sizes from documentation.
        """
        plans = {
            "mtn": [
                {"id": "1gb", "name": "MTN 1GB (SME)"},
                {"id": "2gb", "name": "MTN 2GB (SME)"},
                {"id": "5gb", "name": "MTN 5GB (SME)"},
                {"id": "1gb1d", "name": "MTN 1GB Daily"},
            ],
            "glo": [
                {"id": "500MB", "name": "GLO 500MB (CG)"},
                {"id": "1GB", "name": "GLO 1GB (CG)"},
                {"id": "10GB", "name": "GLO 10GB (CG)"},
            ],
            "airtel": [
                {"id": "1gb1w", "name": "Airtel 1GB Weekly"},
                {"id": "2gb1m", "name": "Airtel 2GB Monthly"},
                {"id": "35gb1m", "name": "Airtel 35GB Monthly"},
            ]
        }
        
        if network_id:
            return plans.get(network_id.lower(), [])
        
        # Return all plans flattened
        return [item for sublist in plans.values() for item in sublist]

    def get_cable_tv_packages(self, service_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return []

    def get_electricity_services(self) -> List[Dict[str, Any]]:
        return []

    def get_internet_packages(self) -> List[Dict[str, Any]]:
        return []

    def get_education_services(self) -> List[Dict[str, Any]]:
        return []