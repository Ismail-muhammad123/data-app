import requests
import logging
from typing import Dict, Any, List
from django.conf import settings
from ..interfaces import BaseVTUProvider

logger = logging.getLogger(__name__)

class KetamencyProvider(BaseVTUProvider):
    """
    Ketamency Smile (Internet Only) Provider Implementation
    """

    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key")
        self.base_url = "https://smileapi.ketawancy.com/api/v1/external"

        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }

    @property
    def provider_name(self) -> str:
        return "ketamency"

    @classmethod
    def get_supported_services(cls) -> List[str]:
        return ["internet"]  # ONLY internet supported

    @classmethod
    def get_config_requirements(cls) -> List[Dict[str, Any]]:
        return [
            {"name": "api_key", "label": "API Key", "type": "text", "required": True},
        ]

    # =========================
    # INTERNAL REQUEST HANDLER
    # =========================
    def _get(self, endpoint: str) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            timeout = getattr(settings, "KETAMENCY_TIMEOUT", 30)
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ketamency GET error: {e}")
            raise Exception(f"Ketamency API error: {e}")

    def _post(self, endpoint: str, payload: dict) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            timeout = getattr(settings, "KETAMENCY_TIMEOUT", 30)
            response = requests.post(url, json=payload, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ketamency POST error: {e}")
            raise Exception(f"Ketamency API error: {e}")

    # =========================
    # INTERNET PURCHASE
    # =========================
    def buy_internet(
        self,
        plan_id: str,
        phone: str,
        amount: float,
        reference: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Purchase Smile data bundle
        """
        # Automatically infer numberType from phone prefix if not provided
        number_type = kwargs.get("number_type")
        if number_type is None:
             number_type = "phone" if (str(phone).startswith("0702") or str(phone).startswith("234")) else "account"

        payload = {
            "planId": plan_id,
            "phoneNumber": phone,
            "numberType": number_type,
            "idempotencyKey": reference
        }

        endpoint = "/purchase"
        res = self._post(endpoint, payload)

        status = "PENDING"
        if res.get("status") == "success":
            status = "SUCCESS"
        elif res.get("status") == "error":
            status = "FAILED"

        return {
            "status": status,
            "provider_reference": res.get("data", {}).get("transactionId"),
            "message": res.get("message"),
            "raw_response": res
        }

    # =========================
    # VALIDATIONS
    # =========================
    def verify_internet(self, accountID: str, **kwargs) -> Dict[str, Any]:
        """
        Entry point for VerifyCustomerView (purchase_type='internet')
        """
        if str(accountID).startswith("0702") or str(accountID).startswith("234"):
            res = self.validate_phone(accountID)
            res["number_type"] = "phone"
        else:
            res = self.validate_account(accountID)
            res["number_type"] = "account"
        
        if "status" not in res:
            res["status"] = "SUCCESS" if res.get("account_name") else "FAILED"
        
        return res

    def validate_account(self, account_number: str) -> Dict[str, Any]:
        """
        Verify Smile account
        """
        endpoint = "/verify-account"

        res = self._post(endpoint, {
            "accountNumber": account_number
        })
        if res.get("status") == "success":
            first_name = res.get("data", {}).get("customer", {}).get("firstName", "")
            middle_name = res.get("data", {}).get("customer", {}).get("middleName", "")
            last_name = res.get("data", {}).get("customer", {}).get("lastName", "")
            return {
                "status": "SUCCESS",
                "account_name": f"{first_name} {middle_name} {last_name}".strip(),
                "raw_response": res
            }
        
        return {"status": "FAILED", "account_name": None, "raw_response": res}

    def validate_phone(self, phone: str) -> Dict[str, Any]:
        """
        Verify Smile phone number
        """
        endpoint = "/verify-phone"

        res = self._post(endpoint, {
            "phoneNumber": phone
        })

        if res.get("status") == "success":

            first_name = res.get("data", {}).get("customer", {}).get("firstName", "")
            middle_name = res.get("data", {}).get("customer", {}).get("middleName", "")
            last_name = res.get("data", {}).get("customer", {}).get("lastName", "")
            return {
                "status": "SUCCESS",
                "account_name": f"{first_name} {middle_name} {last_name}".strip(),
                "raw_response": res
            }
        
        return {"status": "FAILED", "account_name": None, "raw_response": res}

    # =========================
    # WALLET
    # =========================
    def get_wallet_balance(self) -> float:
        try:
            res = self._get("/user")
            if res.get("status") == "success":
                return float(res['data']['wallet'] + res['data']['bonus'])
            return 0.0
        except:
            return 0.0

    # =========================
    # SERVICES / PLANS
    # =========================
    def get_available_services(self) -> List[Dict[str, Any]]:
        return [
            {"type": "internet", "endpoint": "/plans"},
        ]

    def sync_internet(self) -> int:
        res = self._get("/plans")
        if res.get("status") == "success":
            return self._deserialize_internet(res)
        return 0

    def _deserialize_internet(self, res: Dict[str, Any]) -> int:
        from orders.models import InternetService, InternetVariation
        from summary.models import SiteConfig
        from decimal import Decimal

        plans = res.get("data", [])
        provider_config = getattr(self, "provider_config", None)

        config = SiteConfig.objects.first()
        margin = config.internet_margin if config else Decimal("0.00")


        service, _ = InternetService.objects.get_or_create(
            service_id="smile",
            provider=provider_config,
            defaults={"service_name": "Smile"}
        )

        count = 0

        for plan in plans:
            plan_id = plan.get("code")
            name = plan.get("name")
            amount = Decimal(str(plan.get("amount", 0)))

            if not plan_id:
                continue

            InternetVariation.objects.update_or_create(
                variation_id=plan_id,
                service=service,
                defaults={
                    "name": name,
                    "cost_price": amount,
                    "selling_price": amount + margin,
                    "agent_price": amount,
                    "is_active": True
                }
            )
            count += 1

        return count

    # =========================
    # TRANSACTION QUERY
    # =========================
    def query_transaction(self, reference: str) -> Dict[str, Any]:
        return {
            "status": "PENDING",
            "raw_response": {}
        }

    def cancel_transaction(self, reference: str) -> Dict[str, Any]:
        return {
            "status": "FAILED",
            "raw_response": {}
        }

    # =========================
    # WEBHOOKS / CALLBACKS
    # =========================
    def handle_webhook(self, data: Dict[str, Any]) -> bool:
        logger.info(f"Ketamency webhook: {data}")
        return True

    def handle_callback(self, data: Dict[str, Any]) -> bool:
        return self.handle_webhook(data)

    # =========================
    # REQUIRED INTERFACE STUBS
    # =========================
    def buy_airtime(self, *args, **kwargs): return {"status": "FAILED", "message": "Airtime not supported"}
    def buy_data(self, *args, **kwargs): return {"status": "FAILED", "message": "Data not supported"}
    def buy_tv(self, *args, **kwargs): return {"status": "FAILED", "message": "TV not supported"}
    def buy_electricity(self, *args, **kwargs): return {"status": "FAILED", "message": "Electricity not supported"}
    def buy_education(self, *args, **kwargs): return {"status": "FAILED", "message": "Education not supported"}
    def validate_meter(self, *args, **kwargs): return {"status": "FAILED", "account_name": "N/A", "raw_response": {}}
    def validate_cable_id(self, *args, **kwargs): return {"status": "FAILED", "account_name": "N/A", "raw_response": {}}
    def sync_airtime(self): return 0
    def sync_data(self): return 0
    def sync_cable(self): return 0
    def sync_electricity(self): return 0
    def sync_education(self): return 0
