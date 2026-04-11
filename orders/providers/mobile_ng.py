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
                p_amount = Decimal(str(plan.get("amount", 0)))
                variation, _ = DataVariation.objects.update_or_create(
                    variation_id=str(plan.get("code")),
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

        # Popular TV service IDs for MobileNig
        tv_services = [('AKA', 'GOtv'), ('AKB', 'DStv'), ('AKC', 'StarTimes')]
        created_variations = []
        for sid, name in tv_services:
            service, _ = TVService.objects.get_or_create(
                service_id=sid,
                defaults={
                    "service_name": name,
                    "provider": getattr(self, "provider_config", None),
                }
            )
            packages = self.get_cable_tv_packages(sid)
            for pkg in packages:
                p_amount = Decimal(str(pkg.get("amount", 0)))
                variation, _ = TVVariation.objects.update_or_create(
                    variation_id=str(pkg.get("code")),
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
        # Implementation depends on dynamic listing which is complex for MobileNig
        return 0

    def sync_internet(self) -> int:
        return 0

    def sync_education(self) -> int:
        from orders.models import EducationService, EducationVariation
        from summary.models import SiteConfig
        from decimal import Decimal
        config = SiteConfig.objects.first()
        margin = config.education_margin if config else Decimal('0.00')

        services = self.get_education_services()
        created_variations = []
        for svc in services:
            service, _ = EducationService.objects.get_or_create(
                service_id=svc["id"],
                defaults={
                    "service_name": svc["name"],
                    "provider": getattr(self, "provider_config", None),
                }
            )
            variation, _ = EducationVariation.objects.update_or_create(
                variation_id=f"{svc['id']}-general",
                service=service,
                defaults={
                    "name": "PIN Purchase",
                    "cost_price": Decimal('0.00'),
                    "selling_price": margin,
                    "agent_price": Decimal('0.00'),
                    "is_active": True,
                }
            )
            created_variations.append(variation)
        return len(created_variations)

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