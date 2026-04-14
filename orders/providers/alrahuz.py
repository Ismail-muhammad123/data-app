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
        url = config.get('base_url')
        if url:
            self.base_url = url.rstrip('/')
        else:
            self.base_url = 'https://alrahuzdata.com.ng'
        
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
            print(f"Alrahuz {method} {url} - Payload: {data} - Status: {response.status_code} - Response: {response.text}")
            return response.json()
        except Exception as e:
            logger.error(f"Alrahuz request error: {str(e)}")
            raise Exception(f"Alrahuz API error: {str(e)}")

    def buy_airtime(self, phone: str, network: str, amount: float, reference: str) -> Dict[str, Any]:
        network_map = {'mtn': 1, 'airtel': 2, 'glo': 3, '9mobile': 4}
        
        payload = {
            "network": network_map.get(network.lower(), 1),
            "amount": int(amount),
            "mobile_number": phone,
            "Ported_number": True,
            "airtime_type": "VTU"
        }
        
        res = self._request("POST", "/api/topup/", payload)
        
        status = "SUCCESS" if res.get('Status') == 'successful' or res.get('status') == 'successful' or (res.get("Status") and "success" in res.get("Status").lower()) or (res.get("status") and "success" in res.get("status").lower()) else "FAILED"
        return {
            "status": status,
            "provider_reference": res.get('id', reference),
            "raw_response": res
        }

    def buy_data(self, phone: str, network: str, plan_id: str, amount: float, reference: str) -> Dict[str, Any]:
        network_map = {'mtn': 1, 'airtel': 2, 'glo': 3, '9mobile': 4}
        
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

        provider_config = getattr(self, "provider_config", None)
        networks = self.get_airtime_networks()
        created = []
        for net_data in networks:
            net, _ = AirtimeNetwork.objects.update_or_create(
                service_id=str(net_data["id"]),
                provider=provider_config,
                defaults={
                    "service_name": net_data["name"],
                    "cost_price": base_100,
                    "selling_price": base_100 + margin,
                    "agent_price": base_100,
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

        provider_config = getattr(self, "provider_config", None)
        plans = self.get_data_plans()
        created_variations = []
        for plan in plans:
            service, _ = DataService.objects.get_or_create(
                service_id=plan["network"],
                provider=provider_config,
                defaults={
                    "service_name": plan["network"],
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

        provider_config = getattr(self, "provider_config", None)
        packages = self.get_cable_tv_packages()
        created_variations = []
        for pkg in packages:
            service, _ = TVService.objects.get_or_create(
                service_id=pkg["id"],
                provider=provider_config,
                defaults={
                    "service_name": pkg["name"],
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

        provider_config = getattr(self, "provider_config", None)
        discos = self.get_electricity_services()
        created_variations = []
        for disco in discos:
            service, _ = ElectricityService.objects.get_or_create(
                service_id=str(disco["id"]),
                provider=provider_config,
                defaults={
                    "service_name": disco["name"],
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
            {"id": 2, "name": "AIRTEL"},
            {"id": 3, "name": "GLO"},
            {"id": 4, "name": "9MOBILE"}
        ]

    def get_data_plans(self, network_id: Optional[str] = None) -> List[Dict[str, Any]]:
        # Updated from documentation provided by user
        all_plans = [
            # AIRTEL
            {"id": "162", "network": "AIRTEL", "name": "CORPORATE 500 MB", "amount": 485},
            {"id": "164", "network": "AIRTEL", "name": "CORPORATE 1 GB", "amount": 780},
            {"id": "165", "network": "AIRTEL", "name": "CORPORATE 2 GB", "amount": 1480},
            {"id": "166", "network": "AIRTEL", "name": "CORPORATE 3 GB", "amount": 1950},
            {"id": "167", "network": "AIRTEL", "name": "CORPORATE 4 GB", "amount": 2500},
            {"id": "168", "network": "AIRTEL", "name": "CORPORATE 5 GB", "amount": 3500},
            {"id": "169", "network": "AIRTEL", "name": "CORPORATE 6 GB", "amount": 4000},
            {"id": "170", "network": "AIRTEL", "name": "CORPORATE 8 GB", "amount": 4500},
            {"id": "171", "network": "AIRTEL", "name": "CORPORATE 10 GB", "amount": 5000},
            {"id": "175", "network": "AIRTEL", "name": "CORPORATE 12 GB", "amount": 5500},
            {"id": "176", "network": "AIRTEL", "name": "CORPORATE 13 GB", "amount": 6000},
            {"id": "177", "network": "AIRTEL", "name": "CORPORATE 18 GB", "amount": 7500},
            {"id": "178", "network": "AIRTEL", "name": "CORPORATE 25 GB", "amount": 9500},
            {"id": "179", "network": "AIRTEL", "name": "CORPORATE 35 GB", "amount": 11000},
            {"id": "180", "network": "AIRTEL", "name": "CORPORATE 60 GB", "amount": 15000},
            {"id": "181", "network": "AIRTEL", "name": "CORPORATE 100 GB", "amount": 20000},
            {"id": "182", "network": "AIRTEL", "name": "CORPORATE 160 GB", "amount": 30000},
            {"id": "183", "network": "AIRTEL", "name": "CORPORATE 210 GB", "amount": 40000},
            {"id": "184", "network": "AIRTEL", "name": "CORPORATE 300 GB", "amount": 50000},
            {"id": "185", "network": "AIRTEL", "name": "CORPORATE 350 GB", "amount": 60000},
            {"id": "188", "network": "AIRTEL", "name": "CORPORATE 650 GB", "amount": 100000},
            {"id": "237", "network": "AIRTEL", "name": "CORPORATE 1 500 MB", "amount": 485},
            {"id": "238", "network": "AIRTEL", "name": "CORPORATE 1 1 GB", "amount": 780},
            {"id": "239", "network": "AIRTEL", "name": "CORPORATE 1 1.5 GB", "amount": 1000},
            {"id": "240", "network": "AIRTEL", "name": "CORPORATE 1 2 GB", "amount": 1479},
            {"id": "241", "network": "AIRTEL", "name": "CORPORATE 1 3 GB", "amount": 2000},
            {"id": "242", "network": "AIRTEL", "name": "CORPORATE 1 5 GB", "amount": 2500},
            {"id": "243", "network": "AIRTEL", "name": "CORPORATE 1 6 GB", "amount": 3000},
            {"id": "244", "network": "AIRTEL", "name": "CORPORATE 1 7 GB", "amount": 3400},
            {"id": "245", "network": "AIRTEL", "name": "CORPORATE 1 10 GB", "amount": 4000},
            {"id": "190", "network": "AIRTEL", "name": "GIFTING 300 MB", "amount": 100},
            {"id": "191", "network": "AIRTEL", "name": "GIFTING 600 MB", "amount": 230},
            {"id": "194", "network": "AIRTEL", "name": "GIFTING 1.5 GB", "amount": 500},
            {"id": "195", "network": "AIRTEL", "name": "GIFTING 2 GB", "amount": 600},
            {"id": "196", "network": "AIRTEL", "name": "GIFTING 3 GB", "amount": 750},
            {"id": "197", "network": "AIRTEL", "name": "GIFTING 3.2 GB", "amount": 850},
            {"id": "198", "network": "AIRTEL", "name": "GIFTING 4 GB", "amount": 2450},
            {"id": "199", "network": "AIRTEL", "name": "GIFTING 5 GB", "amount": 3400},
            {"id": "200", "network": "AIRTEL", "name": "GIFTING 6 GB", "amount": 3950},
            {"id": "201", "network": "AIRTEL", "name": "GIFTING 8 GB", "amount": 4400},
            {"id": "202", "network": "AIRTEL", "name": "GIFTING 10 GB", "amount": 4900},
            {"id": "203", "network": "AIRTEL", "name": "GIFTING 12 GB", "amount": 5300},
            {"id": "204", "network": "AIRTEL", "name": "GIFTING 13 GB", "amount": 5500},
            {"id": "205", "network": "AIRTEL", "name": "GIFTING 18 GB", "amount": 7500},
            {"id": "206", "network": "AIRTEL", "name": "GIFTING 25 GB", "amount": 9500},
            {"id": "207", "network": "AIRTEL", "name": "GIFTING 35 GB", "amount": 11000},
            {"id": "208", "network": "AIRTEL", "name": "GIFTING 60 GB", "amount": 15000},
            {"id": "209", "network": "AIRTEL", "name": "GIFTING 100 GB", "amount": 20000},
            {"id": "210", "network": "AIRTEL", "name": "GIFTING 160 GB", "amount": 30000},
            {"id": "211", "network": "AIRTEL", "name": "GIFTING 210 GB", "amount": 40000},
            {"id": "212", "network": "AIRTEL", "name": "GIFTING 300 GB", "amount": 50000},
            {"id": "213", "network": "AIRTEL", "name": "GIFTING 350 GB", "amount": 60000},
            {"id": "214", "network": "AIRTEL", "name": "GIFTING 650 GB", "amount": 100000},

            # MTN
            {"id": "82", "network": "MTN", "name": "SME 500 MB", "amount": 350},
            {"id": "83", "network": "MTN", "name": "SME 1 GB", "amount": 450},
            {"id": "84", "network": "MTN", "name": "SME 2 GB", "amount": 900},
            {"id": "86", "network": "MTN", "name": "SME 3 GB", "amount": 1350},
            {"id": "87", "network": "MTN", "name": "SME 5 GB", "amount": 1700},
            {"id": "88", "network": "MTN", "name": "SME 10 GB", "amount": 4500},
            {"id": "89", "network": "MTN", "name": "SME 20 GB", "amount": 9000},
            {"id": "215", "network": "MTN", "name": "SME 25 GB", "amount": 12000},
            {"id": "91", "network": "MTN", "name": "GIFTING 500 MB", "amount": 300},
            {"id": "92", "network": "MTN", "name": "GIFTING 1 GB", "amount": 450},
            {"id": "93", "network": "MTN", "name": "GIFTING 2 GB", "amount": 750},
            {"id": "94", "network": "MTN", "name": "GIFTING 2.5 GB", "amount": 900},
            {"id": "95", "network": "MTN", "name": "GIFTING 3.2 GB", "amount": 1000},
            {"id": "96", "network": "MTN", "name": "GIFTING 5 GB", "amount": 1750},
            {"id": "97", "network": "MTN", "name": "GIFTING 6 GB", "amount": 2500},
            {"id": "98", "network": "MTN", "name": "GIFTING 11 GB", "amount": 3500},
            {"id": "99", "network": "MTN", "name": "GIFTING 20 GB", "amount": 5000},
            {"id": "100", "network": "MTN", "name": "GIFTING 25 GB", "amount": 9000},
            {"id": "101", "network": "MTN", "name": "GIFTING 30 GB", "amount": 9500},
            {"id": "102", "network": "MTN", "name": "GIFTING 35 GB", "amount": 7500},
            {"id": "103", "network": "MTN", "name": "GIFTING 40 GB", "amount": 10000},
            {"id": "104", "network": "MTN", "name": "GIFTING 60 GB", "amount": 14500},
            {"id": "105", "network": "MTN", "name": "GIFTING 65 GB", "amount": 16000},
            {"id": "106", "network": "MTN", "name": "GIFTING 75 GB", "amount": 18000},
            {"id": "107", "network": "MTN", "name": "GIFTING 90 GB", "amount": 25000},
            {"id": "108", "network": "MTN", "name": "GIFTING 150 GB", "amount": 40000},
            {"id": "109", "network": "MTN", "name": "GIFTING 165 GB", "amount": 45000},
            {"id": "110", "network": "MTN", "name": "GIFTING 200 GB", "amount": 50000},
            {"id": "111", "network": "MTN", "name": "GIFTING 250 GB", "amount": 60000},
            {"id": "112", "network": "MTN", "name": "GIFTING 450 GB", "amount": 75000},
            {"id": "113", "network": "MTN", "name": "GIFTING 800 GB", "amount": 130000},
            {"id": "231", "network": "MTN", "name": "DATA SHARE 2 GB", "amount": 800},
            {"id": "232", "network": "MTN", "name": "DATA SHARE 3 GB", "amount": 1200},
            {"id": "233", "network": "MTN", "name": "DATA SHARE 5 GB", "amount": 1600},
            {"id": "234", "network": "MTN", "name": "DATA SHARE 1 GB", "amount": 400},
            {"id": "235", "network": "MTN", "name": "DATA SHARE 10 GB", "amount": 4490},
            {"id": "236", "network": "MTN", "name": "DATA SHARE 20 GB", "amount": 5500},
            {"id": "246", "network": "MTN", "name": "DATA SHARE 500 MB", "amount": 350},
            {"id": "122", "network": "MTN", "name": "OFFERS 3.2 GB", "amount": 980},
            {"id": "123", "network": "MTN", "name": "OFFERS 3.5 GB", "amount": 1000},
            {"id": "125", "network": "MTN", "name": "OFFERS 4 GB", "amount": 1200},
            {"id": "126", "network": "MTN", "name": "OFFERS 5.5 GB", "amount": 1500},
            {"id": "230", "network": "MTN", "name": "OFFERS 7 GB", "amount": 1800},

            # 9MOBILE
            {"id": "144", "network": "9MOBILE", "name": "CORPORATE 300 MB", "amount": 100},
            {"id": "145", "network": "9MOBILE", "name": "CORPORATE 500 MB", "amount": 200},
            {"id": "146", "network": "9MOBILE", "name": "CORPORATE 1 GB", "amount": 400},
            {"id": "147", "network": "9MOBILE", "name": "CORPORATE 2 GB", "amount": 800},
            {"id": "148", "network": "9MOBILE", "name": "CORPORATE 3 GB", "amount": 1200},
            {"id": "149", "network": "9MOBILE", "name": "CORPORATE 5 GB", "amount": 2000},
            {"id": "150", "network": "9MOBILE", "name": "CORPORATE 10 GB", "amount": 4000},
            {"id": "151", "network": "9MOBILE", "name": "CORPORATE 15 GB", "amount": 6000},
            {"id": "152", "network": "9MOBILE", "name": "CORPORATE 20 GB", "amount": 8000},
            {"id": "153", "network": "9MOBILE", "name": "GIFTING 300 MB", "amount": 100},
            {"id": "154", "network": "9MOBILE", "name": "GIFTING 500 MB", "amount": 200},
            {"id": "155", "network": "9MOBILE", "name": "GIFTING 1 GB", "amount": 400},
            {"id": "156", "network": "9MOBILE", "name": "GIFTING 2 GB", "amount": 800},
            {"id": "157", "network": "9MOBILE", "name": "GIFTING 3 GB", "amount": 1200},
            {"id": "158", "network": "9MOBILE", "name": "GIFTING 5 GB", "amount": 2000},
            {"id": "159", "network": "9MOBILE", "name": "GIFTING 10 GB", "amount": 4000},
            {"id": "160", "network": "9MOBILE", "name": "GIFTING 15 GB", "amount": 6000},
            {"id": "161", "network": "9MOBILE", "name": "GIFTING 20 GB", "amount": 8000},

            # GLO
            {"id": "127", "network": "GLO", "name": "CORPORATE 200 MB", "amount": 100},
            {"id": "128", "network": "GLO", "name": "CORPORATE 500 MB", "amount": 200},
            {"id": "129", "network": "GLO", "name": "CORPORATE 1 GB", "amount": 400},
            {"id": "130", "network": "GLO", "name": "CORPORATE 2 GB", "amount": 850},
            {"id": "131", "network": "GLO", "name": "CORPORATE 3 GB", "amount": 1200},
            {"id": "132", "network": "GLO", "name": "CORPORATE 5 GB", "amount": 2000},
            {"id": "133", "network": "GLO", "name": "CORPORATE 10 GB", "amount": 4000},
            {"id": "134", "network": "GLO", "name": "GIFTING 200 MB", "amount": 95},
            {"id": "135", "network": "GLO", "name": "GIFTING 750 MB", "amount": 200},
            {"id": "136", "network": "GLO", "name": "GIFTING 1 GB", "amount": 350},
            {"id": "137", "network": "GLO", "name": "GIFTING 1.5 GB", "amount": 380},
            {"id": "138", "network": "GLO", "name": "GIFTING 2 GB", "amount": 500},
            {"id": "139", "network": "GLO", "name": "GIFTING 2.5 GB", "amount": 550},
            {"id": "140", "network": "GLO", "name": "GIFTING 5.1 GB", "amount": 1000},
            {"id": "141", "network": "GLO", "name": "GIFTING 7.7 GB", "amount": 2500},
            {"id": "142", "network": "GLO", "name": "GIFTING 10 GB", "amount": 1950},
            {"id": "143", "network": "GLO", "name": "GIFTING 14 GB", "amount": 3900},
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