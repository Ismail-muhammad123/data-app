import requests
import logging
from typing import Dict, Any, List, Optional
from ..interfaces import BaseVTUProvider

logger = logging.getLogger(__name__)

# =============================================================================
# Hardcoded plan catalogs — Arewa Global does not expose listing endpoints.
# Update plan IDs and prices from the Arewa Global dashboard as needed.
# =============================================================================

AIRTIME_NETWORKS_DATA = [
    {"service_id": "1", "service_name": "MTN", "min_amount": "50", "max_amount": "50000"},
    {"service_id": "2", "service_name": "Airtel", "min_amount": "50", "max_amount": "50000"},
    {"service_id": "3", "service_name": "Glo", "min_amount": "50", "max_amount": "50000"},
    {"service_id": "4", "service_name": "9mobile", "min_amount": "50", "max_amount": "50000"},
]

DATA_PLANS_BY_NETWORK = {
    "1": {
        "name": "MTN",
        "plans": [
            {"plan_id": "1", "name": "MTN SME 500MB (30 Days)", "selling_price": 140, "plan_type": "sme"},
            {"plan_id": "2", "name": "MTN SME 1GB (30 Days)", "selling_price": 219, "plan_type": "sme"},
            {"plan_id": "3", "name": "MTN SME 2GB (30 Days)", "selling_price": 440, "plan_type": "sme"},
            {"plan_id": "4", "name": "MTN SME 3GB (30 Days)", "selling_price": 660, "plan_type": "sme"},
            {"plan_id": "5", "name": "MTN SME 5GB (30 Days)", "selling_price": 1100, "plan_type": "sme"},
            {"plan_id": "6", "name": "MTN SME 10GB (30 Days)", "selling_price": 2200, "plan_type": "sme"},
            {"plan_id": "7", "name": "MTN CG 500MB (30 Days)", "selling_price": 145, "plan_type": "corporate"},
            {"plan_id": "8", "name": "MTN CG 1GB (30 Days)", "selling_price": 280, "plan_type": "corporate"},
            {"plan_id": "9", "name": "MTN CG 2GB (30 Days)", "selling_price": 560, "plan_type": "corporate"},
            {"plan_id": "10", "name": "MTN CG 3GB (30 Days)", "selling_price": 840, "plan_type": "corporate"},
            {"plan_id": "11", "name": "MTN CG 5GB (30 Days)", "selling_price": 1400, "plan_type": "corporate"},
            {"plan_id": "12", "name": "MTN CG 10GB (30 Days)", "selling_price": 2800, "plan_type": "corporate"},
            {"plan_id": "13", "name": "MTN Direct 500MB (30 Days)", "selling_price": 150, "plan_type": "direct"},
            {"plan_id": "14", "name": "MTN Direct 1GB (30 Days)", "selling_price": 300, "plan_type": "direct"},
            {"plan_id": "15", "name": "MTN Direct 2GB (30 Days)", "selling_price": 600, "plan_type": "direct"},
            {"plan_id": "16", "name": "MTN Direct 3GB (30 Days)", "selling_price": 900, "plan_type": "direct"},
            {"plan_id": "17", "name": "MTN Direct 5GB (30 Days)", "selling_price": 1500, "plan_type": "direct"},
            {"plan_id": "18", "name": "MTN Direct 10GB (30 Days)", "selling_price": 3000, "plan_type": "direct"},
        ]
    },
    "2": {
        "name": "Airtel",
        "plans": [
            {"plan_id": "19", "name": "Airtel CG 500MB (30 Days)", "selling_price": 140, "plan_type": "corporate"},
            {"plan_id": "20", "name": "Airtel CG 1GB (30 Days)", "selling_price": 280, "plan_type": "corporate"},
            {"plan_id": "21", "name": "Airtel CG 2GB (30 Days)", "selling_price": 560, "plan_type": "corporate"},
            {"plan_id": "22", "name": "Airtel CG 3GB (30 Days)", "selling_price": 840, "plan_type": "corporate"},
            {"plan_id": "23", "name": "Airtel CG 5GB (30 Days)", "selling_price": 1400, "plan_type": "corporate"},
            {"plan_id": "24", "name": "Airtel CG 10GB (30 Days)", "selling_price": 2800, "plan_type": "corporate"},
            {"plan_id": "25", "name": "Airtel Direct 500MB (30 Days)", "selling_price": 150, "plan_type": "direct"},
            {"plan_id": "26", "name": "Airtel Direct 1GB (30 Days)", "selling_price": 300, "plan_type": "direct"},
            {"plan_id": "27", "name": "Airtel Direct 2GB (30 Days)", "selling_price": 600, "plan_type": "direct"},
            {"plan_id": "28", "name": "Airtel Direct 5GB (30 Days)", "selling_price": 1500, "plan_type": "direct"},
        ]
    },
    "3": {
        "name": "Glo",
        "plans": [
            {"plan_id": "29", "name": "Glo CG 500MB (30 Days)", "selling_price": 140, "plan_type": "corporate"},
            {"plan_id": "30", "name": "Glo CG 1GB (30 Days)", "selling_price": 280, "plan_type": "corporate"},
            {"plan_id": "31", "name": "Glo CG 2GB (30 Days)", "selling_price": 560, "plan_type": "corporate"},
            {"plan_id": "32", "name": "Glo CG 3GB (30 Days)", "selling_price": 840, "plan_type": "corporate"},
            {"plan_id": "33", "name": "Glo CG 5GB (30 Days)", "selling_price": 1400, "plan_type": "corporate"},
            {"plan_id": "34", "name": "Glo CG 10GB (30 Days)", "selling_price": 2800, "plan_type": "corporate"},
            {"plan_id": "35", "name": "Glo Direct 500MB (30 Days)", "selling_price": 150, "plan_type": "direct"},
            {"plan_id": "36", "name": "Glo Direct 1GB (30 Days)", "selling_price": 300, "plan_type": "direct"},
            {"plan_id": "37", "name": "Glo Direct 2GB (30 Days)", "selling_price": 600, "plan_type": "direct"},
            {"plan_id": "38", "name": "Glo Direct 5GB (30 Days)", "selling_price": 1500, "plan_type": "direct"},
        ]
    },
    "4": {
        "name": "9mobile",
        "plans": [
            {"plan_id": "39", "name": "9mobile CG 500MB (30 Days)", "selling_price": 140, "plan_type": "corporate"},
            {"plan_id": "40", "name": "9mobile CG 1GB (30 Days)", "selling_price": 280, "plan_type": "corporate"},
            {"plan_id": "41", "name": "9mobile CG 2GB (30 Days)", "selling_price": 560, "plan_type": "corporate"},
            {"plan_id": "42", "name": "9mobile CG 3GB (30 Days)", "selling_price": 840, "plan_type": "corporate"},
            {"plan_id": "43", "name": "9mobile CG 5GB (30 Days)", "selling_price": 1400, "plan_type": "corporate"},
            {"plan_id": "44", "name": "9mobile Direct 500MB (30 Days)", "selling_price": 150, "plan_type": "direct"},
            {"plan_id": "45", "name": "9mobile Direct 1GB (30 Days)", "selling_price": 300, "plan_type": "direct"},
            {"plan_id": "46", "name": "9mobile Direct 2GB (30 Days)", "selling_price": 600, "plan_type": "direct"},
            {"plan_id": "47", "name": "9mobile Direct 5GB (30 Days)", "selling_price": 1500, "plan_type": "direct"},
        ]
    },
}

INTERNET_SERVICES = {
    "smile": {
        "name": "Smile",
        "endpoint": "/api/smile-data/",
        "plans": [
            {"plan_id": "16", "name": "Smile Mini 1GB", "selling_price": 450},
            {"plan_id": "17", "name": "Smile Midi 2GB", "selling_price": 800},
            {"plan_id": "18", "name": "Smile Maxi 5GB", "selling_price": 1800},
            {"plan_id": "19", "name": "Smile Mega 6.5GB", "selling_price": 2200},
            {"plan_id": "20", "name": "Smile 10GB", "selling_price": 3000},
            {"plan_id": "21", "name": "Smile 15GB", "selling_price": 4500},
            {"plan_id": "22", "name": "Smile 20GB", "selling_price": 5500},
            {"plan_id": "23", "name": "Smile Unlimited Lite", "selling_price": 6500},
        ]
    },
    "kirani": {
        "name": "Kirani",
        "endpoint": "/api/kirani/",
        "plans": [
            {"plan_id": "1", "name": "Kirani 500 Minutes", "selling_price": 500},
            {"plan_id": "2", "name": "Kirani 1000 Minutes", "selling_price": 1000},
            {"plan_id": "3", "name": "Kirani 2000 Minutes", "selling_price": 2000},
            {"plan_id": "4", "name": "Kirani 5000 Minutes", "selling_price": 5000},
        ]
    },
    "alpha": {
        "name": "Alpha",
        "endpoint": "/api/alpha/",
        "plans": [
            {"plan_id": "1", "name": "Alpha 500 Caller", "selling_price": 500},
            {"plan_id": "2", "name": "Alpha 1000 Caller", "selling_price": 1000},
            {"plan_id": "3", "name": "Alpha 2000 Caller", "selling_price": 2000},
            {"plan_id": "4", "name": "Alpha 5000 Caller", "selling_price": 5000},
        ]
    },
}


class ArewaGlobalProvider(BaseVTUProvider):
    """
    Arewa Global implementation of BaseVTUProvider.
    Documentation: https://arewaglobal.co/documentation.php
    """

    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://arewaglobal.co').rstrip('/')
        
        self.headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
        }

    @property
    def provider_name(self) -> str:
        return "arewaglobal"

    @classmethod
    def get_supported_services(cls) -> List[str]:
        return ['airtime', 'data', 'internet']

    @classmethod
    def get_config_requirements(cls) -> List[Dict[str, Any]]:
        return [
            {
                'name': 'api_key', 
                'label': 'API Token', 
                'type': 'text', 
                'required': True,
                'help_text': 'Get this from your profile on arewaglobal.co'
            },
            {
                'name': 'base_url', 
                'label': 'Base URL', 
                'type': 'text', 
                'required': False, 
                'default': 'https://arewaglobal.co'
            }
        ]

    def _post(self, endpoint: str, data: dict) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, json=data, headers=self.headers, timeout=30)
            return response.json()
        except Exception as e:
            logger.error(f"ArewaGlobal request error: {str(e)}")
            raise Exception(f"ArewaGlobal API error: {str(e)}")

    # -------------------------------------------------------------------------
    # Purchase methods
    # -------------------------------------------------------------------------

    def buy_airtime(self, phone: str, network: str, amount: float, reference: str) -> Dict[str, Any]:
        network_map = {'mtn': '1', 'airtel': '2', 'glo': '3', '9mobile': '4'}
        network_id = network_map.get(network.lower(), '1')

        payload = {
            "phone": phone,
            "amount": int(amount),
            "network": network_id,
            "ported_number": "true"
        }
        
        res = self._post("/api/airtime/", payload)
        
        status = "SUCCESS" if res.get('status') == 'success' else "FAILED"
        return {
            "status": status,
            "provider_reference": res.get('id', reference),
            "message": res.get('msg'),
            "raw_response": res
        }

    def buy_data(self, phone: str, network: str, plan_id: str, amount: float, reference: str) -> Dict[str, Any]:
        network_map = {'mtn': '1', 'airtel': '2', 'glo': '3', '9mobile': '4'}
        network_id = network_map.get(network.lower(), '1')

        payload = {
            "phone": phone,
            "plan": plan_id,
            "network": network_id,
            "ported_number": "true"
        }
        
        res = self._post("/api/data/", payload)
        
        status = "SUCCESS" if res.get('status') == 'success' else "FAILED"
        return {
            "status": status,
            "provider_reference": res.get('id', reference),
            "message": res.get('msg'),
            "raw_response": res
        }

    def buy_tv(self, tv_id: str, package_id: str, smart_card_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        """ArewaGlobal does not support TV."""
        return {"status": "FAILED", "message": "TV payments not supported on ArewaGlobal"}

    def buy_electricity(self, disco_id: str, plan_id: str, meter_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        """ArewaGlobal does not support Electricity."""
        return {"status": "FAILED", "message": "Electricity payments not supported on ArewaGlobal"}

    def buy_education(self, exam_type: str, variation_id: str, quantity: int, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        """ArewaGlobal does not support Education pins."""
        return {"status": "FAILED", "message": "Education payments not supported on ArewaGlobal"}

    def buy_internet(self, plan_id: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        """
        Internet subscription payment routed by service type to the correct Arewa endpoint.
        """
        service_type = kwargs.get('internet_variation', plan_id) # Typically we pass the actual variation id / plan name
        # We need to extract the service key like smile, alpha from the variation_id since we prepended it in sync: f"{service_key}_{plan_id}"
        service_key = plan_id.split('_')[0].lower() if '_' in plan_id else service_type.lower()
        if '_' in plan_id:
            plan_id = plan_id.split('_')[-1]
        
        if service_key == 'smile':
            endpoint = "/api/smile-data/"
            payload = {
                "PhoneNumber": phone,
                "BundleTypeCode": plan_id,
                "actype": "AccountNumber"
            }
        elif service_key == 'alpha':
            endpoint = "/api/alpha/"
            payload = {"phone": phone, "planid": plan_id}
        elif service_key == 'kirani':
            endpoint = "/api/kirani/"
            payload = {"phone": phone, "planid": plan_id}
        else:
            raise ValueError(f"Unsupported internet service type for ArewaGlobal: {service_key}")

        res = self._post(endpoint, payload)
        
        status = "SUCCESS" if res.get('status') == 'success' else "FAILED"
        return {
            "status": status,
            "provider_reference": res.get('id'),
            "message": res.get('msg'),
            "raw_response": res
        }

    # -------------------------------------------------------------------------
    # Transaction & webhook handling
    # -------------------------------------------------------------------------

    def query_transaction(self, reference: str) -> Dict[str, Any]:
        res = self._post("/api/user/", {})
        return {"status": "UNKNOWN", "raw_response": res}

    def cancel_transaction(self, reference: str) -> Dict[str, Any]:
        """Not supported on ArewaGlobal."""
        return {"status": "FAILED", "message": "Cancellation not supported"}

    def handle_webhook(self, data: Dict[str, Any]) -> bool:
        return data.get("status") == "success"

    def handle_callback(self, data: Dict[str, Any]) -> bool:
        return self.handle_webhook(data)

    # -------------------------------------------------------------------------
    # Validation stubs (not supported by Arewa Global)
    # -------------------------------------------------------------------------

    def validate_meter(self, meter_number: str, service: str) -> Dict[str, Any]:
        return {"account_name": "N/A", "raw_response": {}}

    def validate_cable_id(self, card_number: str, service: str) -> Dict[str, Any]:
        return {"account_name": "N/A", "raw_response": {}}

    # -------------------------------------------------------------------------
    # Wallet
    # -------------------------------------------------------------------------

    def get_wallet_balance(self) -> float:
        res = self._post("/api/user/", {})
        try:
            return float(res.get('balance', 0))
        except (ValueError, TypeError):
            return 0.0

    def get_available_services(self) -> List[Dict[str, Any]]:
        return [
            {"type": "airtime", "endpoint": "/api/airtime/"},
            {"type": "data", "endpoint": "/api/data/"},
            {"type": "internet", "sub_services": list(INTERNET_SERVICES.keys())},
        ]

    # -------------------------------------------------------------------------
    # Airtime networks  (hardcoded — synced to DB)
    # -------------------------------------------------------------------------

    def sync_airtime(self) -> int:
        """
        Persists hardcoded airtime networks to the database.
        """
        from orders.models import AirtimeNetwork

        created = []
        for net_data in AIRTIME_NETWORKS_DATA:
            net, _ = AirtimeNetwork.objects.update_or_create(
                service_id=net_data["service_id"],
                defaults={
                    "service_name": net_data["service_name"],
                    "min_amount": net_data["min_amount"],
                    "max_amount": net_data["max_amount"],
                    "provider": getattr(self, "provider_config", None),
                }
            )
            created.append(net)
        return len(created)

    # -------------------------------------------------------------------------
    # Data plans  (hardcoded — synced to DB)
    # -------------------------------------------------------------------------

    def sync_data(self) -> int:
        """
        Persists hardcoded data plans to the database.
        """
        from orders.models import DataService, DataVariation

        networks_to_sync = DATA_PLANS_BY_NETWORK

        created_variations = []
        for net_id, net_info in networks_to_sync.items():
            service, _ = DataService.objects.update_or_create(
                service_id=net_id,
                defaults={
                    "service_name": net_info["name"],
                    "provider": getattr(self, "provider_config", None),
                }
            )
            for plan in net_info["plans"]:
                variation, _ = DataVariation.objects.update_or_create(
                    variation_id=plan["plan_id"],
                    service=service,
                    defaults={
                        "name": plan["name"],
                        "selling_price": plan["selling_price"],
                        "plan_type": plan.get("plan_type", "general"),
                        "is_active": True,
                    }
                )
                created_variations.append(variation)

        return len(created_variations)

    # -------------------------------------------------------------------------
    # Internet packages  (Smile, Kirani, Ratel, Alpha — synced to DB)
    # -------------------------------------------------------------------------

    def sync_internet(self) -> int:
        """
        Persists hardcoded internet service plans (Smile, Kirani, Ratel, Alpha).
        """
        from orders.models import InternetService, InternetVariation

        services = []
        count = 0
        for service_key, svc_data in INTERNET_SERVICES.items():
            service, _ = InternetService.objects.update_or_create(
                service_id=service_key,
                defaults={
                    "service_name": svc_data["name"],
                    "provider": getattr(self, "provider_config", None),
                }
            )
            for plan in svc_data["plans"]:
                InternetVariation.objects.update_or_create(
                    variation_id=f"{service_key}_{plan['plan_id']}",
                    defaults={
                        "name": plan["name"],
                        "service": service,
                        "selling_price": plan["selling_price"],
                        "is_active": True,
                    }
                )
                count += 1
            services.append(service)

        return count

    # -------------------------------------------------------------------------
    # Unsupported service stubs
    # -------------------------------------------------------------------------

    def sync_cable(self) -> int:
        return 0

    def sync_electricity(self) -> int:
        return 0

    def sync_education(self) -> int:
        return 0