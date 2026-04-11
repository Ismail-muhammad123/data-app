import requests
import logging
from typing import Dict, Any, List, Optional
from ..interfaces import BaseVTUProvider

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

    def buy_tv(self, tv_id: str, package_id: str, smart_card_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        cable_map = {'gotv': 1, 'dstv': 2, 'startimes': 3}
        payload = {
            "cablename": cable_map.get(tv_id.lower()),
            "cableplan": package_id,
            "smart_card_number": smart_card_number
        }
        res = self._request("POST", "/api/cablesub/", payload)
        status = "SUCCESS" if res.get('Status') == 'success' else "FAILED"
        
        return {
            "status": status,
            "provider_reference": res.get('id'),
            "raw_response": res
        }

    def buy_electricity(self, disco_id: str, plan_id: str, meter_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        payload = {
            "disco_name": disco_id, # Use Disco ID
            "amount": int(amount),
            "meter_number": meter_number,
            "Meter_Type": kwargs.get('meter_type', 'Prepaid')
        }
        res = self._request("POST", "/api/billpayment/", payload)
        status = "SUCCESS" if res.get('Status') == 'success' else "FAILED"
        
        return {
            "status": status,
            "provider_reference": res.get('id'),
            "raw_response": res
        }

    def buy_internet(self, plan_id: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Internet service not supported by Alrahuz."}

    def buy_education(self, exam_type: str, variation_id: str, quantity: int, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Education service not supported by Alrahuz."}

    def query_transaction(self, reference: str) -> Dict[str, Any]:
        # Documentation specifies querying by the ID returned during creation
        res = self._request("GET", f"/api/data/{reference}")
        return {"status": "SUCCESS" if res.get('Status') == 'success' else "FAILED", "raw_response": res}

    def cancel_transaction(self, reference: str) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Cancellation not supported by Alrahuz."}

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
                service_id=str(net_data["id"]),
                defaults={
                    "service_name": net_data["name"],
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
                service_id=plan["network"],
                defaults={
                    "service_name": plan["network"],
                    "provider": getattr(self, "provider_config", None),
                }
            )
            p_amount = Decimal(str(plan["amount"]))
            variation, _ = DataVariation.objects.update_or_create(
                variation_id=plan["id"],
                service=service,
                defaults={
                    "name": plan["name"],
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
                service_id=pkg["cable"],
                defaults={
                    "service_name": pkg["cable"],
                    "provider": getattr(self, "provider_config", None),
                }
            )
            p_amount = Decimal(str(pkg["amount"]))
            variation, _ = TVVariation.objects.update_or_create(
                variation_id=pkg["id"],
                service=service,
                defaults={
                    "name": pkg["name"],
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
                service_id=str(disco["id"]),
                defaults={
                    "service_name": disco["name"],
                    "provider": getattr(self, "provider_config", None),
                }
            )
            variation, _ = ElectricityVariation.objects.update_or_create(
                variation_id=f"{disco['id']}-general",
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