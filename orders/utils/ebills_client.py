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
