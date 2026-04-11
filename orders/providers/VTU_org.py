import requests
import logging
from typing import Dict, Any, List, Optional
from ..interfaces import BaseVTUProvider

logger = logging.getLogger(__name__)

class VTUOrgProvider(BaseVTUProvider):
    """
    VTU.ng implementation of BaseVTUProvider.
    Documentation: https://vtu.ng/api/
    """

    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://vtu.ng/wp-json/api/v2').rstrip('/')
        
        self.headers = {
            "Authorization": f"Token {self.api_key}", # Alternative auth method supported
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    @property
    def provider_name(self) -> str:
        return "vtuorg"

    @classmethod
    def get_supported_services(cls) -> List[str]:
        return ['airtime', 'data', 'tv', 'electricity', 'education']

    @classmethod
    def get_config_requirements(cls) -> List[Dict[str, Any]]:
        return [
            {'name': 'api_key', 'label': 'API Key', 'type': 'text', 'required': True},
            {'name': 'base_url', 'label': 'Base URL', 'type': 'text', 'required': False, 'default': 'https://vtu.ng/wp-json/api/v2'}
        ]

    def _request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # VTU.ng often expects the api_key in params even for POST
        params = params or {}
        params.update({"api_key": self.api_key})
        
        try:
            response = requests.request(method, url, json=data, params=params, timeout=30)
            return response.json()
        except Exception as e:
            logger.error(f"VTUOrg request error: {str(e)}")
            raise Exception(f"VTUOrg API error: {str(e)}")

    def buy_airtime(self, phone: str, network: str, amount: float, reference: str) -> Dict[str, Any]:
        """
        Purchase airtime (VTU).
        """
        payload = {
            "network": network.lower(),
            "amount": int(amount),
            "phone": phone,
            "airtime_type": "vtu"
        }
        
        res = self._request("POST", "airtime", data=payload)
        
        status = "FAILED"
        if res.get('status') == 'success':
            status = "SUCCESS"
        elif res.get('status') == 'processing':
            status = "PENDING"
            
        return {
            "status": status,
            "provider_reference": res.get('order_id', reference),
            "message": res.get('message'),
            "raw_response": res
        }

    def buy_data(self, phone: str, network: str, plan_id: str, amount: float, reference: str) -> Dict[str, Any]:
        """
        Purchase a data bundle using its variation_id.
        """
        payload = {
            "network": network.lower(),
            "variation_id": plan_id,
            "phone": phone
        }
        
        res = self._request("POST", "data", data=payload)
        
        status = "SUCCESS" if res.get('status') == 'success' else "FAILED"
        return {
            "status": status,
            "provider_reference": res.get('order_id', reference),
            "raw_response": res
        }

    def buy_tv(self, tv_id: str, package_id: str, smart_card_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        payload = {
            "service_id": tv_id.lower(),
            "variation_id": package_id,
            "phone": smart_card_number,
            "amount": int(amount)
        }
        res = self._request("POST", "tv", data=payload)
        status = "SUCCESS" if res.get('status') == 'success' else "FAILED"
        return {
            "status": status,
            "provider_reference": res.get('order_id'),
            "raw_response": res
        }

    def buy_electricity(self, disco_id: str, plan_id: str, meter_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        payload = {
            "service_id": disco_id.lower(),
            "variation_id": plan_id,
            "phone": meter_number,
            "amount": int(amount)
        }
        res = self._request("POST", "electricity", data=payload)
        status = "SUCCESS" if res.get('status') == 'success' else "FAILED"
        return {
            "status": status,
            "provider_reference": res.get('order_id'),
            "raw_response": res
        }

    def buy_internet(self, plan_id: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Internet service not supported by VTUOrg."}

    def buy_education(self, exam_type: str, variation_id: str, quantity: int, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        payload = {
            "service_id": exam_type.lower(),
            "variation_id": variation_id,
            "phone": kwargs.get('phone', ''),
            "amount": int(amount)
        }
        res = self._request("POST", "education", data=payload)
        status = "SUCCESS" if res.get('status') == 'success' else "FAILED"
        return {
            "status": status,
            "provider_reference": res.get('order_id'),
            "raw_response": res
        }

    def query_transaction(self, reference: str) -> Dict[str, Any]:
        """
        Requery a specific order status.
        """
        res = self._request("GET", f"requery/{reference}")
        return {
            "status": "SUCCESS" if res.get('status') == 'success' else "PENDING",
            "raw_response": res
        }

    def cancel_transaction(self, reference: str) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Cancellation not supported by VTUOrg."}

    def handle_webhook(self, data: Dict[str, Any]) -> bool:
        return data.get('status') == 'success'

    def handle_callback(self, data: Dict[str, Any]) -> bool:
        return self.handle_webhook(data)

    def validate_meter(self, meter_number: str, service: str) -> Dict[str, Any]:
        res = self._request("GET", f"verify-customer?service_id={service}&customer_id={meter_number}")
        return {"account_name": res.get('customer_name'), "raw_response": res}

    def validate_cable_id(self, card_number: str, service: str) -> Dict[str, Any]:
        res = self._request("GET", f"verify-customer?service_id={service}&customer_id={card_number}")
        return {"account_name": res.get('customer_name'), "raw_response": res}

    def get_wallet_balance(self) -> float:
        res = self._request("GET", "balance")
        return float(res.get('balance', 0))

    def get_available_services(self) -> List[Dict[str, Any]]:
        return [{"type": "airtime"}, {"type": "data"}, {"type": "tv"}, {"type": "electricity"}]

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

        networks = self.get_airtime_networks()
        created_variations = []
        for net in networks:
            service, _ = DataService.objects.get_or_create(
                service_id=str(net["id"]),
                defaults={
                    "service_name": net["name"],
                    "provider": getattr(self, "provider_config", None),
                }
            )
            plans = self.get_data_plans(net["id"])
            for plan in plans:
                p_amount = Decimal(str(plan.get("variation_amount") or 0))
                variation, _ = DataVariation.objects.update_or_create(
                    variation_id=str(plan.get("variation_id")),
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

        services = ['dstv', 'gotv', 'startimes']
        created_variations = []
        for sid in services:
            service, _ = TVService.objects.get_or_create(
                service_id=sid,
                defaults={
                    "service_name": sid.upper(),
                    "provider": getattr(self, "provider_config", None),
                }
            )
            packages = self.get_cable_tv_packages(sid)
            for pkg in packages:
                p_amount = Decimal(str(pkg.get("variation_amount") or 0))
                variation, _ = TVVariation.objects.update_or_create(
                    variation_id=str(pkg.get("variation_id")),
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
            service_id = disco.get("service_id") or disco.get("variation_id")
            service, _ = ElectricityService.objects.get_or_create(
                service_id=service_id,
                defaults={
                    "service_name": disco.get("name"),
                    "provider": getattr(self, "provider_config", None),
                }
            )
            variation, _ = ElectricityVariation.objects.update_or_create(
                variation_id=f"{service_id}-general",
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
        from orders.models import EducationService, EducationVariation
        from summary.models import SiteConfig
        from decimal import Decimal
        config = SiteConfig.objects.first()
        margin = config.education_margin if config else Decimal('0.00')

        exams = self.get_education_services()
        created_variations = []
        for exam in exams:
            service_id = exam.get("service_id") or exam.get("variation_id")
            service, _ = EducationService.objects.get_or_create(
                service_id=service_id,
                defaults={
                    "service_name": exam.get("name"),
                    "provider": getattr(self, "provider_config", None),
                }
            )
            p_amount = Decimal(str(exam.get("variation_amount") or 0))
            variation, _ = EducationVariation.objects.update_or_create(
                variation_id=str(exam.get("variation_id")),
                service=service,
                defaults={
                    "name": exam.get("name"),
                    "cost_price": p_amount,
                    "selling_price": p_amount + margin,
                    "agent_price": p_amount,
                    "is_active": True,
                }
            )
            created_variations.append(variation)
        return len(created_variations)

    def get_airtime_networks(self) -> List[Dict[str, Any]]:
        return [
            {"id": "mtn", "name": "MTN"},
            {"id": "glo", "name": "Glo"},
            {"id": "airtel", "name": "Airtel"},
            {"id": "9mobile", "name": "9mobile"}
        ]

    def get_data_plans(self, network_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Dynamically fetches data variations from the API.
        """
        endpoint = f"variations/data?service_id={network_id}" if network_id else "variations/data"
        res = self._request("GET", endpoint)
        return res.get('variations', [])

    def get_cable_tv_packages(self, service_id: Optional[str] = None) -> List[Dict[str, Any]]:
        endpoint = f"variations/tv?service_id={service_id}" if service_id else "variations/tv"
        res = self._request("GET", endpoint)
        return res.get('variations', [])

    def get_electricity_services(self) -> List[Dict[str, Any]]:
        res = self._request("GET", "variations/electricity")
        return res.get('variations', [])

    def get_education_services(self) -> List[Dict[str, Any]]:
        res = self._request("GET", "variations/education")
        return res.get('variations', [])