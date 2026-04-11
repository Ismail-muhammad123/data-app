import requests
import logging
from typing import Dict, Any, List, Optional
from ..interfaces import BaseVTUProvider

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

    def buy_tv(self, tv_id: str, package_id: str, smart_card_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Cable TV not supported by SMEData."}

    def buy_electricity(self, disco_id: str, plan_id: str, meter_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Electricity not supported by SMEData."}

    def buy_internet(self, plan_id: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Internet service not supported by SMEData."}

    def buy_education(self, exam_type: str, variation_id: str, quantity: int, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Education service not supported by SMEData."}

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

    def cancel_transaction(self, reference: str) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Cancellation not supported by SMEData."}

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
                service_id=plan.get("network", "MTN"),
                defaults={
                    "service_name": plan.get("network", "MTN"),
                    "provider": getattr(self, "provider_config", None),
                }
            )
            p_amount = Decimal(str(plan.get("amount") or 0))
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
        from orders.models import TVService, TVVariation
        from summary.models import SiteConfig
        from decimal import Decimal
        config = SiteConfig.objects.first()
        margin = config.tv_margin if config else Decimal('0.00')

        packages = self.get_cable_tv_packages()
        created_variations = []
        for pkg in packages:
            service, _ = TVService.objects.get_or_create(
                service_id=pkg.get("cable", "GOTV"),
                defaults={
                    "service_name": pkg.get("cable", "GOTV"),
                    "provider": getattr(self, "provider_config", None),
                }
            )
            p_amount = Decimal(str(pkg.get("amount") or 0))
            variation, _ = TVVariation.objects.update_or_create(
                variation_id=str(pkg.get("id")),
                service=service,
                defaults={
                    "name": pkg.get("name"),
                    "cost_price": p_amount,
                    "selling_price": p_amount + margin,
                    "agent_price": p_amount,
                    "is_active": True,
                }
            )
            created_variations.append(variation)
        return len(created_variations)

    def sync_electricity(self) -> int:
        from orders.models import ElectricityService, ElectricityVariation
        from summary.models import SiteConfig
        from decimal import Decimal
        config = SiteConfig.objects.first()
        margin = config.electricity_margin if config else Decimal('0.00')

        discos = self.get_electricity_services()
        created_variations = []
        for disco in discos:
            service, _ = ElectricityService.objects.get_or_create(
                service_id=str(disco.get("id")),
                defaults={
                    "service_name": disco.get("name"),
                    "provider": getattr(self, "provider_config", None),
                }
            )
            variation, _ = ElectricityVariation.objects.update_or_create(
                variation_id=f"{disco.get('id')}-general",
                service=service,
                defaults={
                    "name": "General Setup",
                    "cost_price": Decimal('0.00'),
                    "selling_price": margin,
                    "agent_price": Decimal('0.00'),
                    "is_active": True,
                }
            )
            created_variations.append(variation)
        return len(created_variations)

    def sync_internet(self) -> int:
        return 0

    def sync_education(self) -> int:
        return 0

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