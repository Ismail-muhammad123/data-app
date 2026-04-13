import requests
import logging
from typing import Dict, Any, List, Optional
from ..interfaces import BaseVTUProvider

logger = logging.getLogger(__name__)

# =============================================================================
# Hardcoded plan catalogs — FlowPay plan IDs and prices from documentation.
# =============================================================================

AIRTIME_NETWORKS_DATA = [
    {"service_id": "1", "service_name": "MTN", "min_amount": "50", "max_amount": "50000"},
    {"service_id": "2", "service_name": "Airtel", "min_amount": "50", "max_amount": "50000"},
    {"service_id": "3", "service_name": "Glo", "min_amount": "50", "max_amount": "50000"},
    {"service_id": "4", "service_name": "9mobile", "min_amount": "50", "max_amount": "50000"},
]

DATA_PLANS_BY_NETWORK = {
    # ── MTN (network id "1") ────────────────────────────────────────────
    "1": {
        "name": "MTN",
        "plans": [
            # SME
            {"plan_id": "82", "name": "MTN SME 500 MB", "selling_price": 116, "plan_type": "sme", "validity": "30 DAYS"},
            {"plan_id": "83", "name": "MTN SME 1 GB", "selling_price": 232, "plan_type": "sme", "validity": "30 DAYS"},
            {"plan_id": "84", "name": "MTN SME 2 GB", "selling_price": 464, "plan_type": "sme", "validity": "30 DAYS"},
            {"plan_id": "86", "name": "MTN SME 3 GB", "selling_price": 696, "plan_type": "sme", "validity": "30 DAYS"},
            {"plan_id": "87", "name": "MTN SME 5 GB", "selling_price": 1160, "plan_type": "sme", "validity": "30 DAYS"},
            {"plan_id": "88", "name": "MTN SME 10 GB", "selling_price": 2320, "plan_type": "sme", "validity": "30 DAYS"},
            {"plan_id": "89", "name": "MTN SME 20 GB", "selling_price": 4640, "plan_type": "sme", "validity": "30 DAYS"},
            {"plan_id": "215", "name": "MTN SME 25 GB", "selling_price": 5800, "plan_type": "sme", "validity": "30 DAYS"},
            # GIFTING
            {"plan_id": "91", "name": "MTN GIFTING 500 MB", "selling_price": 143, "plan_type": "gifting", "validity": "2 DAYS"},
            {"plan_id": "92", "name": "MTN GIFTING 1 GB", "selling_price": 286, "plan_type": "gifting", "validity": "7 DAYS"},
            {"plan_id": "93", "name": "MTN GIFTING 2 GB", "selling_price": 571, "plan_type": "gifting", "validity": "2 DAYS"},
            {"plan_id": "94", "name": "MTN GIFTING 2.5 GB", "selling_price": 714, "plan_type": "gifting", "validity": "2 DAYS"},
            {"plan_id": "95", "name": "MTN GIFTING 3.2 GB", "selling_price": 913, "plan_type": "gifting", "validity": "2 DAYS"},
            {"plan_id": "96", "name": "MTN GIFTING 5 GB", "selling_price": 1427, "plan_type": "gifting", "validity": "7 DAYS"},
            {"plan_id": "97", "name": "MTN GIFTING 6 GB", "selling_price": 1713, "plan_type": "gifting", "validity": "7 DAYS"},
            {"plan_id": "98", "name": "MTN GIFTING 11 GB", "selling_price": 3140, "plan_type": "gifting", "validity": "7 DAYS"},
            {"plan_id": "99", "name": "MTN GIFTING 20 GB", "selling_price": 5708, "plan_type": "gifting", "validity": "7 DAYS"},
            {"plan_id": "100", "name": "MTN GIFTING 25 GB", "selling_price": 7134, "plan_type": "gifting", "validity": "30 DAYS"},
            {"plan_id": "101", "name": "MTN GIFTING 30 GB", "selling_price": 8560, "plan_type": "gifting", "validity": "BROADBAND 30 DAYS"},
            {"plan_id": "102", "name": "MTN GIFTING 35 GB", "selling_price": 9987, "plan_type": "gifting", "validity": "POSTPAID 30 DAYS"},
            {"plan_id": "103", "name": "MTN GIFTING 40 GB", "selling_price": 11414, "plan_type": "gifting", "validity": "POSTPAID 60 DAYS"},
            {"plan_id": "104", "name": "MTN GIFTING 60 GB", "selling_price": 17120, "plan_type": "gifting", "validity": "BROADBAND 30 DAYS"},
            {"plan_id": "105", "name": "MTN GIFTING 65 GB", "selling_price": 18546, "plan_type": "gifting", "validity": "30 DAYS"},
            {"plan_id": "106", "name": "MTN GIFTING 75 GB", "selling_price": 21398, "plan_type": "gifting", "validity": "30 DAYS"},
            {"plan_id": "107", "name": "MTN GIFTING 90 GB", "selling_price": 25679, "plan_type": "gifting", "validity": "60 DAYS"},
            {"plan_id": "108", "name": "MTN GIFTING 150 GB", "selling_price": 42797, "plan_type": "gifting", "validity": "60 DAYS"},
            {"plan_id": "109", "name": "MTN GIFTING 165 GB", "selling_price": 47076, "plan_type": "gifting", "validity": "60 DAYS"},
            {"plan_id": "110", "name": "MTN GIFTING 200 GB", "selling_price": 57061, "plan_type": "gifting", "validity": "60 DAYS"},
            {"plan_id": "111", "name": "MTN GIFTING 250 GB", "selling_price": 71325, "plan_type": "gifting", "validity": "60 DAYS"},
            {"plan_id": "112", "name": "MTN GIFTING 450 GB", "selling_price": 128384, "plan_type": "gifting", "validity": "BROADBAND 90 DAYS"},
            {"plan_id": "113", "name": "MTN GIFTING 800 GB", "selling_price": 228238, "plan_type": "gifting", "validity": "60 DAYS"},
            # DATA SHARE
            {"plan_id": "234", "name": "MTN DATA SHARE 1 GB", "selling_price": 228, "plan_type": "gifting", "validity": "30 DAYS"},
            {"plan_id": "231", "name": "MTN DATA SHARE 2 GB", "selling_price": 456, "plan_type": "gifting", "validity": "30 DAYS"},
            {"plan_id": "232", "name": "MTN DATA SHARE 3 GB", "selling_price": 684, "plan_type": "gifting", "validity": "30 DAYS"},
            {"plan_id": "233", "name": "MTN DATA SHARE 5 GB", "selling_price": 1140, "plan_type": "gifting", "validity": "30 DAYS"},
            {"plan_id": "235", "name": "MTN DATA SHARE 10 GB", "selling_price": 2280, "plan_type": "gifting", "validity": "30 DAYS"},
            {"plan_id": "236", "name": "MTN DATA SHARE 20 GB", "selling_price": 4561, "plan_type": "gifting", "validity": "30 DAYS"},
            {"plan_id": "246", "name": "MTN DATA SHARE 500 MB", "selling_price": 114, "plan_type": "gifting", "validity": "30 DAYS"},
            # OFFERS
            {"plan_id": "122", "name": "MTN OFFERS 3.2 GB", "selling_price": 980, "plan_type": "gifting", "validity": "2 DAYS"},
            {"plan_id": "123", "name": "MTN OFFERS 3.5 GB", "selling_price": 1000, "plan_type": "gifting", "validity": "2 DAYS"},
            {"plan_id": "125", "name": "MTN OFFERS 4 GB", "selling_price": 1200, "plan_type": "gifting", "validity": "2 DAYS"},
            {"plan_id": "126", "name": "MTN OFFERS 5.5 GB", "selling_price": 1500, "plan_type": "gifting", "validity": "2 DAYS"},
            {"plan_id": "230", "name": "MTN OFFERS 7 GB", "selling_price": 1800, "plan_type": "gifting", "validity": "2 DAYS"},
        ]
    },
    # ── Airtel (network id "2") ─────────────────────────────────────────
    "2": {
        "name": "Airtel",
        "plans": [
            # CORPORATE
            {"plan_id": "162", "name": "Airtel CORPORATE 500 MB", "selling_price": 116, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "164", "name": "Airtel CORPORATE 1 GB", "selling_price": 232, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "165", "name": "Airtel CORPORATE 2 GB", "selling_price": 464, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "166", "name": "Airtel CORPORATE 3 GB", "selling_price": 696, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "167", "name": "Airtel CORPORATE 4 GB", "selling_price": 928, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "168", "name": "Airtel CORPORATE 5 GB", "selling_price": 1160, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "169", "name": "Airtel CORPORATE 6 GB", "selling_price": 1392, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "170", "name": "Airtel CORPORATE 8 GB", "selling_price": 1856, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "171", "name": "Airtel CORPORATE 10 GB", "selling_price": 2320, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "175", "name": "Airtel CORPORATE 12 GB", "selling_price": 2784, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "176", "name": "Airtel CORPORATE 13 GB", "selling_price": 3016, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "177", "name": "Airtel CORPORATE 18 GB", "selling_price": 4176, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "178", "name": "Airtel CORPORATE 25 GB", "selling_price": 5800, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "179", "name": "Airtel CORPORATE 35 GB", "selling_price": 8120, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "180", "name": "Airtel CORPORATE 60 GB", "selling_price": 13920, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "181", "name": "Airtel CORPORATE 100 GB", "selling_price": 23200, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "182", "name": "Airtel CORPORATE 160 GB", "selling_price": 37120, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "183", "name": "Airtel CORPORATE 210 GB", "selling_price": 48720, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "184", "name": "Airtel CORPORATE 300 GB", "selling_price": 69600, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "185", "name": "Airtel CORPORATE 350 GB", "selling_price": 81200, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "188", "name": "Airtel CORPORATE 650 GB", "selling_price": 150800, "plan_type": "corporate", "validity": "90 DAYS"},
            # CORPORATE 1
            {"plan_id": "237", "name": "Airtel CORPORATE 1 500 MB", "selling_price": 175, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "238", "name": "Airtel CORPORATE 1 1 GB", "selling_price": 350, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "239", "name": "Airtel CORPORATE 1 1.5 GB", "selling_price": 525, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "240", "name": "Airtel CORPORATE 1 2 GB", "selling_price": 700, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "241", "name": "Airtel CORPORATE 1 3 GB", "selling_price": 1050, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "242", "name": "Airtel CORPORATE 1 5 GB", "selling_price": 1750, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "243", "name": "Airtel CORPORATE 1 6 GB", "selling_price": 2100, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "244", "name": "Airtel CORPORATE 1 7 GB", "selling_price": 2450, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "245", "name": "Airtel CORPORATE 1 10 GB", "selling_price": 3500, "plan_type": "corporate", "validity": "30 DAYS"},
        ]
    },
    # ── GLO (network id "3") ────────────────────────────────────────────
    "3": {
        "name": "Glo",
        "plans": [
            # CORPORATE
            {"plan_id": "127", "name": "Glo CORPORATE 200 MB", "selling_price": 48, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "128", "name": "Glo CORPORATE 500 MB", "selling_price": 120, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "129", "name": "Glo CORPORATE 1 GB", "selling_price": 240, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "130", "name": "Glo CORPORATE 2 GB", "selling_price": 480, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "131", "name": "Glo CORPORATE 3 GB", "selling_price": 720, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "132", "name": "Glo CORPORATE 5 GB", "selling_price": 1200, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "133", "name": "Glo CORPORATE 10 GB", "selling_price": 2400, "plan_type": "corporate", "validity": "30 DAYS"},
            # GIFTING
            {"plan_id": "134", "name": "Glo GIFTING 200 MB", "selling_price": 95, "plan_type": "gifting", "validity": "1 DAY"},
            {"plan_id": "135", "name": "Glo GIFTING 750 MB", "selling_price": 238, "plan_type": "gifting", "validity": "1 DAY"},
            {"plan_id": "136", "name": "Glo GIFTING 1 GB", "selling_price": 476, "plan_type": "gifting", "validity": "1 DAY"},
            {"plan_id": "137", "name": "Glo GIFTING 1.5 GB", "selling_price": 714, "plan_type": "gifting", "validity": "1 DAY"},
            {"plan_id": "138", "name": "Glo GIFTING 2 GB", "selling_price": 952, "plan_type": "gifting", "validity": "1 DAY"},
            {"plan_id": "139", "name": "Glo GIFTING 2.5 GB", "selling_price": 1190, "plan_type": "gifting", "validity": "2 DAYS"},
            {"plan_id": "140", "name": "Glo GIFTING 5.1 GB", "selling_price": 1904, "plan_type": "gifting", "validity": "SOCIAL 2 DAYS"},
            {"plan_id": "141", "name": "Glo GIFTING 7.7 GB", "selling_price": 2380, "plan_type": "gifting", "validity": "30 DAYS"},
            {"plan_id": "142", "name": "Glo GIFTING 10 GB", "selling_price": 3808, "plan_type": "gifting", "validity": "7 DAYS"},
            {"plan_id": "143", "name": "Glo GIFTING 14 GB", "selling_price": 4760, "plan_type": "gifting", "validity": "30 DAYS"},
        ]
    },
    # ── 9mobile (network id "4") ────────────────────────────────────────
    "4": {
        "name": "9mobile",
        "plans": [
            # CORPORATE
            {"plan_id": "144", "name": "9mobile CORPORATE 300 MB", "selling_price": 43, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "145", "name": "9mobile CORPORATE 500 MB", "selling_price": 72, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "146", "name": "9mobile CORPORATE 1 GB", "selling_price": 144, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "147", "name": "9mobile CORPORATE 2 GB", "selling_price": 288, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "148", "name": "9mobile CORPORATE 3 GB", "selling_price": 432, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "149", "name": "9mobile CORPORATE 5 GB", "selling_price": 720, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "150", "name": "9mobile CORPORATE 10 GB", "selling_price": 1440, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "151", "name": "9mobile CORPORATE 15 GB", "selling_price": 2160, "plan_type": "corporate", "validity": "30 DAYS"},
            {"plan_id": "152", "name": "9mobile CORPORATE 20 GB", "selling_price": 2880, "plan_type": "corporate", "validity": "30 DAYS"},
            # GIFTING
            {"plan_id": "153", "name": "9mobile GIFTING 300 MB", "selling_price": 95, "plan_type": "gifting", "validity": "30 DAYS"},
            {"plan_id": "154", "name": "9mobile GIFTING 500 MB", "selling_price": 158, "plan_type": "gifting", "validity": "30 DAYS"},
            {"plan_id": "155", "name": "9mobile GIFTING 1 GB", "selling_price": 317, "plan_type": "gifting", "validity": "30 DAYS"},
            {"plan_id": "156", "name": "9mobile GIFTING 2 GB", "selling_price": 634, "plan_type": "gifting", "validity": "30 DAYS"},
            {"plan_id": "157", "name": "9mobile GIFTING 3 GB", "selling_price": 951, "plan_type": "gifting", "validity": "30 DAYS"},
            {"plan_id": "158", "name": "9mobile GIFTING 5 GB", "selling_price": 1585, "plan_type": "gifting", "validity": "30 DAYS"},
            {"plan_id": "159", "name": "9mobile GIFTING 10 GB", "selling_price": 3170, "plan_type": "gifting", "validity": "30 DAYS"},
            {"plan_id": "160", "name": "9mobile GIFTING 15 GB", "selling_price": 4755, "plan_type": "gifting", "validity": "30 DAYS"},
            {"plan_id": "161", "name": "9mobile GIFTING 20 GB", "selling_price": 6340, "plan_type": "gifting", "validity": "30 DAYS"},
        ]
    },
}

class FlowPayProvider(BaseVTUProvider):
    """
    FlowPay implementation of BaseVTUProvider.
    """

    def __init__(self, config: Dict[str, Any]):
        self.api_token = config.get('api_key')
        url = config.get('base_url')
        if url and len(url.strip()) > 0:
            self.base_url = url.strip().rstrip('/')
        else:
            self.base_url = 'https://app.flowpay.ng'
        
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @property
    def provider_name(self) -> str:
        return "flowpay"

    @classmethod
    def get_supported_services(cls) -> List[str]:
        return ['data']

    @classmethod
    def get_config_requirements(cls) -> List[Dict[str, Any]]:
        return [
            {
                'name': 'api_key', 
                'label': 'API Token', 
                'type': 'text', 
                'required': True,
                'help_text': 'Bearer Token from FlowPay'
            },
            {
                'name': 'base_url', 
                'label': 'Base URL', 
                'type': 'text', 
                'required': False, 
                'default': ''
            }
        ]

    def _post(self, endpoint: str, data: dict) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, json=data, headers=self.headers, timeout=10)
            print(f"FlowPay POST {url} - Payload: {data} - Status: {response.status_code} - Response: {response.text}")
            return response.json(), response.status_code
        except Exception as e:
            logger.error(f"FlowPay request error: {str(e)}")
            raise Exception(f"FlowPay API error: {str(e)}")

    def buy_airtime(self, phone: str, network: str, amount: float, reference: str) -> Dict[str, Any]:
        network_map = {'mtn': 1, 'airtel': 2, 'glo': 3, '9mobile': 4}
        network_id = network_map.get(network.lower(), 1)

        payload = {
            "mobile_number": phone,
            "amount": str(int(amount)),
            "network": network_id,
        }
        
        res = self._post("/api/airtime", payload)
        
        # Based on example response: "status": "success"
        status = "SUCCESS" if res.get('status') == 'success' else "FAILED"
        return {
            "status": status,
            "provider_reference": res.get('reference', reference),
            "message": res.get('api_response'),
            "raw_response": res
        }

    def buy_data(self, phone: str, network: str, plan_id: str, amount: float, reference: str) -> Dict[str, Any]:
        network_map = {'mtn': 1, 'airtel': 2, 'glo': 3, '9mobile': 4}
        network_id = network_map.get(network.lower(), 1)

        payload = {
            "mobile_number": phone,
            "plan": plan_id,
            "network": network_id,
        }
        
        res, status_code = self._post("/api/data", payload)
        
        status = "SUCCESS" if status_code in [200, 201]  and res.get('status') == 'successful' else "FAILED"
        return {
            "status": status,
            "provider_reference": res.get('reference', reference),
            "message": res.get('api_response'),
            "raw_response": res
        }

    def buy_tv(self, *args, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "TV not supported"}

    def buy_electricity(self, *args, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Electricity not supported"}

    def buy_internet(self, *args, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Internet not supported"}

    def buy_education(self, *args, **kwargs) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Education not supported"}

    def query_transaction(self, reference: str) -> Dict[str, Any]:
        return {"status": "UNKNOWN", "message": "Query not implemented"}

    def cancel_transaction(self, reference: str) -> Dict[str, Any]:
        return {"status": "FAILED", "message": "Cancellation not supported"}

    def handle_webhook(self, data: Dict[str, Any]) -> bool:
        return data.get("status") == "success"

    def handle_callback(self, data: Dict[str, Any]) -> bool:
        return self.handle_webhook(data)

    def validate_meter(self, meter_number: str, service: str) -> Dict[str, Any]:
        return {"account_name": "N/A", "raw_response": {}}

    def validate_cable_id(self, card_number: str, service: str) -> Dict[str, Any]:
        return {"account_name": "N/A", "raw_response": {}}

    def get_wallet_balance(self) -> float:
        # Documentation didn't specify balance endpoint, returning 0
        return 0.0

    def get_available_services(self) -> List[Dict[str, Any]]:
        return [
            {"type": "airtime", "endpoint": "/api/airtime"},
            {"type": "data", "endpoint": "/api/data"},
        ]

    def sync_airtime(self) -> int:
        from orders.models import AirtimeNetwork
        from summary.models import SiteConfig
        from decimal import Decimal
        config = SiteConfig.objects.first()
        margin = config.airtime_margin if config else Decimal('0.00')
        base_100 = Decimal('100.00')

        created = []
        for net_data in AIRTIME_NETWORKS_DATA:
            net, _ = AirtimeNetwork.objects.update_or_create(
                service_id=net_data["service_id"],
                provider=getattr(self, "provider_config", None),
                defaults={
                    "service_name": net_data["service_name"],
                    "min_amount": net_data["min_amount"],
                    "max_amount": net_data["max_amount"],
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

        networks_to_sync = DATA_PLANS_BY_NETWORK

        created_variations = []
        for net_id, net_info in networks_to_sync.items():
            service, _ = DataService.objects.update_or_create(
                service_id=net_id,
                provider=getattr(self, "provider_config", None),
                defaults={
                    "service_name": net_info["name"],
                }
            )
            for plan in net_info["plans"]:
                p_amount = Decimal(str(plan["selling_price"]))
                variation, _ = DataVariation.objects.update_or_create(
                    variation_id=plan["plan_id"],
                    service=service,
                    defaults={
                        "name": plan["name"],
                        "cost_price": p_amount,
                        "selling_price": p_amount + margin,
                        "agent_price": p_amount,
                        "plan_type": plan.get("plan_type", "general"),
                        "is_active": True,
                    }
                )
                created_variations.append(variation)

        logger.info(f"FlowPay: synced {len(created_variations)} data variations")
        return len(created_variations)

    def sync_cable(self) -> int: return 0
    def sync_electricity(self) -> int: return 0
    def sync_internet(self) -> int: return 0
    def sync_education(self) -> int: return 0
