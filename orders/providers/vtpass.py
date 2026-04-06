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
        self.base_url = config.get('base_url')
        if self.base_url is None or self.base_url == '':
            self.base_url = 'https://vtpass.com/api'
            
        self.headers = {
            "api-key": self.api_key,
            "secret-key": self.secret_key,
            "Content-Type": "application/json",
        }

    @property
    def provider_name(self) -> str:
        return "vtpass"

    @classmethod
    def get_supported_services(cls) -> List[str]:
        return ["airtime", "data", "tv", "electricity", "education"]

    @classmethod
    def get_config_requirements(cls) -> List[Dict[str, Any]]:
        return [
            {"name": "api_key", "label": "API Key", "type": "text", "required": True},
            {"name": "public_key", "label": "Public Key", "type": "text", "required": False},
            {"name": "secret_key", "label": "Secret Key", "type": "text", "required": True},
            {"name": "base_url", "label": "Base API URL", "type": "text", "required": False, "default": "https://vtpass.com/api"},
        ]

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

    def buy_tv(self, tv_id: str, package_id: str, smart_card_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        payload = {
            "request_id": reference,
            "serviceID": tv_id, # e.g. dstv, gotv
            "billersCode": smart_card_number,
            "variation_code": package_id,
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

    def buy_electricity(self, disco_id: str, plan_id: str, meter_number: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        payload = {
            "request_id": reference,
            "serviceID": disco_id,
            "billersCode": meter_number,
            "variation_code": plan_id, # usually prepriod/postpaid
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
            "token": res.get('purchased_code'), # mostly for electricity
            "raw_response": res
        }

    def buy_internet(self, plan_id: str, phone: str, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        # Usually requires service_type (smile, spectranet) via kwargs or split
        service_id = kwargs.get('internet_variation', plan_id) # Example fallback
        
        payload = {
            "request_id": reference,
            "serviceID": service_id,
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

    def buy_education(self, exam_type: str, variation_id: str, quantity: int, amount: float, reference: str, **kwargs) -> Dict[str, Any]:
        payload = {
            "request_id": reference,
            "serviceID": exam_type,
            "variation_code": variation_id,
            "amount": float(amount),
            "phone": kwargs.get('phone', '08000000000') # WAEC/JAMB mostly uses pin
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
            "token": res.get('purchased_code'), # mostly for education pins
            "raw_response": res
        }

    def query_transaction(self, reference: str) -> Dict[str, Any]:
        """Check status of VTPass Transaction"""
        res = self._get(f"/requery?request_id={reference}")
        status = "PENDING"
        if res.get('code') == '000':
            content = res.get('content', {})
            trans = content.get('transactions', {})
            v_status = trans.get('status')
            if v_status == 'delivered': status = "SUCCESS"
            elif v_status in ['failed', 'reversed']: status = "FAILED"
            
        return {"status": status, "raw_response": res}

    def cancel_transaction(self, reference: str) -> Dict[str, Any]:
        """Not supported on VTPass."""
        return {"status": "FAILED", "message": "Cancellation not supported"}

    def handle_webhook(self, data: Dict[str, Any]) -> bool:
        """Processes VTpass webhook notifications."""
        from orders.models import Purchase, VTUProviderConfig
        from wallet.utils import fund_wallet

        request_id = data.get("requestId")
        status_ = data.get("content", {}).get("transactions", {}).get("status")
        
        logger.info(f"VTPass Webhook Processing: requestId={request_id}, status={status_}")
        
        try:
            purchase = Purchase.objects.filter(reference=request_id).first()
            if not purchase:
                logger.warning(f"VTPass Webhook: Purchase not found for reference {request_id}")
                return False

            purchase.provider_response = data
            
            if status_ == "delivered":
                purchase.status = "success"
                purchase.save()
            elif status_ in ["failed", "reversed"]:
                self._handle_async_failure(purchase, f"VTPass reported: {status_}")
            
            return True
        except Exception as e:
            logger.error(f"VTPass Webhook Error: {e}")
            return False

    def handle_callback(self, data: Dict[str, Any]) -> bool:
        """Processes VTpass callback redirects."""
        logger.info(f"VTPass Callback Processing: {data}")
        return True

    def _handle_async_failure(self, purchase, error_msg):
        """Internal failure handling delegating to common logic."""
        purchase.last_error = error_msg
        purchase.save()
        
        from orders.utils.purchase_logic import handle_vtu_async_failure
        handle_vtu_async_failure(purchase)

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
            res = self._get("/balance")
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


    def sync_airtime(self) -> int:
        res = self._get("/services?identifier=airtime")
        raw_list = res.get('content', [{}])[0].get('services', []) if isinstance(res.get('content'), list) else []
        return len(self._deserialize_airtime(raw_list))

    def _deserialize_airtime(self, raw_list: List[Dict]) -> List[Any]:
        from orders.models import AirtimeNetwork
        services = []
        for item in raw_list:
            net, _ = AirtimeNetwork.objects.update_or_create(
                service_id=item.get("serviceID"),
                defaults={
                    "service_name": item.get("name"),
                    "provider": getattr(self, "provider_config", None),
                }
            )
            services.append(net)
        return services

    def sync_data(self) -> int:
        res_nets = self._get("/services?identifier=data")
        networks = res_nets.get('content', [{}])[0].get('services', []) if isinstance(res_nets.get('content'), list) else []
        services_list = [n.get("serviceID") for n in networks]
        
        created_variations = []
        for sid in services_list:
            res = self._get(f"/service-variations?serviceID={sid}")
            variations = res.get('content', {}).get('varations', [])
            created_variations.extend(self._deserialize_data(sid, variations))
        return len(created_variations)

    def _deserialize_data(self, sid: str, variations: List[Dict]) -> List[Any]:
        from orders.models import DataService, DataVariation
        created = []
        service, _ = DataService.objects.get_or_create(
            service_id=sid,
            defaults={"service_name": sid.replace("-data", "").upper(), "provider": getattr(self, "provider_config", None)}
        )
        for item in variations:
            variation, _ = DataVariation.objects.update_or_create(
                variation_id=item.get("variation_code"),
                service=service,
                defaults={
                    "name": item.get("name"),
                    "selling_price": item.get("variation_amount", 0),
                    "is_active": True
                }
            )
            created.append(variation)
        return created

    def sync_cable(self) -> int:
        res_nets = self._get("/services?identifier=tv-subscription")
        networks = res_nets.get('content', [{}])[0].get('services', []) if isinstance(res_nets.get('content'), list) else []
        services_list = [n.get("serviceID") for n in networks]
            
        created_variations = []
        for sid in services_list:
            res = self._get(f"/service-variations?serviceID={sid}")
            variations = res.get('content', {}).get('varations', [])
            created_variations.extend(self._deserialize_tv(sid, variations))
        return len(created_variations)

    def _deserialize_tv(self, sid: str, variations: List[Dict]) -> List[Any]:
        from orders.models import TVService, TVVariation
        created = []
        service, _ = TVService.objects.get_or_create(
            service_id=sid,
            defaults={"service_name": sid.upper(), "provider": getattr(self, "provider_config", None)}
        )
        for item in variations:
            variation, _ = TVVariation.objects.update_or_create(
                variation_id=item.get("variation_code"),
                service=service,
                defaults={
                    "name": item.get("name"),
                    "selling_price": item.get("variation_amount", 0),
                    "is_active": True
                }
            )
            created.append(variation)
        return created

    def sync_electricity(self) -> int:
        res = self._get("/services?identifier=electricity-bill")
        raw_list = res.get('content', [{}])[0].get('services', []) if isinstance(res.get('content'), list) else []
        return len(self._deserialize_electricity(raw_list))

    def _deserialize_electricity(self, raw_list: List[Dict]) -> List[Any]:
        from orders.models import ElectricityService, ElectricityVariation
        services = []
        for item in raw_list:
            service, _ = ElectricityService.objects.get_or_create(
                service_id=item.get("serviceID"),
                defaults={
                    "service_name": item.get("name"),
                    "provider": getattr(self, "provider_config", None),
                }
            )
            variation, _ = ElectricityVariation.objects.update_or_create(
                variation_id=f"{item.get('serviceID')}-general",
                service=service,
                defaults={
                    "name": "General Setup",
                    "is_active": True
                }
            )
            services.append(variation)
        return services

    def sync_internet(self) -> int:
        res_nets = self._get("/services?identifier=internet")
        networks = res_nets.get('content', [{}])[0].get('services', []) if isinstance(res_nets.get('content'), list) else []
        created_variations = []
        for n in networks:
            sid = n.get("serviceID")
            res = self._get(f"/service-variations?serviceID={sid}")
            variations = res.get('content', {}).get('varations', [])
            created_variations.extend(self._deserialize_internet(sid, n.get("name"), variations))
        return len(created_variations)

    def _deserialize_internet(self, sid: str, service_name: str, variations: List[Dict]) -> List[Any]:
        from orders.models import InternetService, InternetVariation
        created = []
        service, _ = InternetService.objects.get_or_create(
            service_id=sid,
            defaults={"service_name": service_name, "provider": getattr(self, "provider_config", None)}
        )
        for item in variations:
            variation, _ = InternetVariation.objects.update_or_create(
                variation_id=item.get("variation_code"),
                service=service,
                defaults={
                    "name": item.get("name"),
                    "selling_price": item.get("variation_amount", 0),
                    "is_active": True
                }
            )
            created.append(variation)
        return created

    def sync_education(self) -> int:
        res_nets = self._get("/services?identifier=education")
        networks = res_nets.get('content', [{}])[0].get('services', []) if isinstance(res_nets.get('content'), list) else []
        created_variations = []
        for n in networks:
            sid = n.get("serviceID")
            res = self._get(f"/service-variations?serviceID={sid}")
            variations = res.get('content', {}).get('varations', [])
            created_variations.extend(self._deserialize_education(sid, n.get("name"), variations))
        return len(created_variations)

    def _deserialize_education(self, sid: str, service_name: str, variations: List[Dict]) -> List[Any]:
        from orders.models import EducationService, EducationVariation
        created = []
        service, _ = EducationService.objects.get_or_create(
            service_id=sid,
            defaults={"service_name": service_name, "provider": getattr(self, "provider_config", None)}
        )
        for item in variations:
            variation, _ = EducationVariation.objects.update_or_create(
                variation_id=item.get("variation_code") or f"{sid}-general",
                service=service,
                defaults={
                    "name": item.get("name") or service_name,
                    "selling_price": item.get("variation_amount", 0) or 0,
                    "is_active": True
                }
            )
            created.append(variation)
        if not variations:
            variation, _ = EducationVariation.objects.update_or_create(
                variation_id=f"{sid}-general",
                service=service,
                defaults={
                    "name": "PIN Purchase",
                    "selling_price": 0,
                    "is_active": True
                }
            )
            created.append(variation)
        return created
