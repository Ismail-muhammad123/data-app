import requests
from typing import Optional, Dict, Any
from .config import (
    E_BILLS_BASE_URL,
    E_BILLS_USERNAME,
    E_BILLS_PASSWORD,
    E_BILLS_TIMEOUT
)
from .exceptions import (
    EBillsAPIError,
    AuthenticationError,
    InsufficientBalanceError,
    ValidationError
)


class EBillsClient:
    """
    Python client for eBills Africa VTU API
    """

    def __init__(self):
        self.base_url = E_BILLS_BASE_URL
        self.username = E_BILLS_USERNAME
        self.password = E_BILLS_PASSWORD
        self.timeout = E_BILLS_TIMEOUT
        self._token: Optional[str] = None

    # -------------------------
    # Internal Helpers
    # -------------------------
    def _headers(self) -> Dict[str, str]:
        if not self._token:
            raise AuthenticationError("Authentication token missing")
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        try:
            data = response.json()
        except ValueError:
            raise EBillsAPIError("Invalid JSON response")

        if response.status_code >= 400:
            raise EBillsAPIError(data.get("message", "API request failed"))

        if data.get("code") == "insufficient_funds":
            raise InsufficientBalanceError(data.get("message"))

        if data.get("code") == "missing_fields":
            raise ValidationError(data.get("message"))

        return data



    # -------------------------
    # Authentication
    # -------------------------
    def authenticate(self) -> str:
        """
        Authenticate and cache JWT token
        """
        url = f"{self.base_url}/jwt-auth/v1/token"
        payload = {
            "username": self.username,
            "password": self.password,
        }

        res = requests.post(url, json=payload, timeout=self.timeout)

        if res.status_code != 200:
            raise AuthenticationError("Authentication failed")

        data = res.json()
        self._token = data["token"]
        return self._token

    # -------------------------
    # Wallet
    # -------------------------
    def get_balance(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v2/balance"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    # -------------------------
    # Variations
    # -------------------------
    def get_data_variations(self, service_id: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v2/variations/data"
        params = {"service_id": service_id} if service_id else None
        res = requests.get(url, params=params, timeout=self.timeout)
        return self._handle_response(res)

    # -------------------------
    # Airtime
    # -------------------------
    def buy_airtime(
        self,
        request_id: str,
        phone: str,
        service_id: str,
        amount: int,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v2/airtime"
        payload = {
            "request_id": request_id,
            "phone": phone,
            "service_id": service_id,
            "amount": amount,
        }
        res = requests.post(
            url,
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        return self._handle_response(res)

    # -------------------------
    # Data
    # -------------------------
    def buy_data(
        self,
        request_id: str,
        phone: str,
        service_id: str,
        variation_id: str,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v2/data"
        payload = {
            "request_id": request_id,
            "phone": phone,
            "service_id": service_id,
            "variation_id": variation_id,
        }
        res = requests.post(
            url,
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        return self._handle_response(res)

    # -------------------------
    # Verify Customer
    # -------------------------
    def verify_user(self, service_id: str, customer_id: str, variation_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v2/verify-customer"
        payload = {
            "service_id": service_id,
            "customer_id": str(customer_id),
            "variation_id": variation_id,
        }

        res = requests.post(
            url,
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )

        return self._handle_response(res)


    # -------------------------
    # Get Electricity variations
    # -------------------------
    def electricity_variations(self, service_id: Optional[str] = None) -> Dict[str, Any]:
        ELECTRICITY_PROVIDERS = [   
            {
                "name": "Ikeja (IKEDC): Lagos State (Ikeja)", 
                "service_id": "ikeja-electric"
            },
            {
                "name": "Eko (EKEDC): Lagos State (Eko)",
                "service_id": "eko-electric"
            },
            {
                "name": "Kano (KEDCO): Kano State, Katsina State, Jigawa State",
                "service_id": "kano-electric"
            },
            {
                "name": "Portharcourt (PHED): Rivers, Akwa Ibom, Bayelsa, Cross River",
                "service_id": "portharcourt-electric"
            },
            {
                "name": "Jos (JED): Bauchi, Benue, Gombe, Plateau",
                "service_id": "jos-electric"
            },
            {
                "name": "Ibadan (IBEDC): Oyo, Ogun, Osun, Kwara, Parts of Niger, Ekiti and Kogi States",
                "service_id": "ibadan-electric"
            },
            {
                "name": "Kaduna (KAEDCO): Kaduna, Kebbi, Sokoto, Zamfara",
                "service_id": "kaduna-electric"
            },
            {
                "name": "Abuja (AEDC): Federal Capital Territory (Abuja), Kogi State, Niger State, Nassarawa State",
                "service_id": "abuja-electric"
            },
            {
                "name": "Enugu (EEDC): Anambra State, Enugu State, Imo State, Ebonyi State",
                "service_id": "enugu-electric"
            },
            {
                "name": "Benin (BEDC): Delta, Edo, Ekiti, and Ondo State",
                "service_id": "benin-electric"
            },
            {
                "name": "Aba (ABEDC): Abia State",
                "service_id": "aba-electric"
            },
            {
                "name": "Yola (YEDC): Adamawa, Taraba, Borno, & Yobe",
                "service_id": "yola-electric"
            }
        ]
        return ELECTRICITY_PROVIDERS


    # -------------------------
    # Pay Electricity Bill
    # -------------------------
    def pay_electricity_bill(self, request_id: str, customer_id: str, service_id: str, variation_id: str, amount: int) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v2/electricity"
        payload = {
            "request_id": request_id,
            "customer_id": str(customer_id),
            "service_id": service_id,
            "variation_id": variation_id,
            "amount": amount,
        }
        res = requests.post(
            url,
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        return self._handle_response(res)

    # -------------------------
    # Get Cable/TV variations
    # -------------------------
    def tv_variations(self, service_id: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v2/variations/tv"
        params = {"service_id": service_id} if service_id else None
        res = requests.get(url, params=params, timeout=self.timeout)
        return self._handle_response(res)

    # -------------------------
    # Pay Cable/TV Subscription
    # -------------------------
    def pay_tv_subscription(
            self,
            request_id: str,
            customer_id: str,
            service_id: str,
            subscription_type: str,
            variation_id: str,
            amount: int
        ) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v2/tv-subscription"
        payload = {
            "request_id": request_id,
            "customer_id": str(customer_id),
            "service_id": service_id,
            "subscription_type": subscription_type,
            "variation_id": variation_id,
            "amount": amount,
        }
        res = requests.post(
            url,
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        return self._handle_response(res)

    # -------------------------
    # Requery
    # -------------------------
    def requery(self, request_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v2/requery"
        payload = {"request_id": request_id}
        res = requests.post(
            url,
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        return self._handle_response(res)
