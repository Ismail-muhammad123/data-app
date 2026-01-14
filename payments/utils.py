
import requests
from django.conf import settings
import hmac
import hashlib
import json
from typing import Optional, Dict, Any
import base64
from datetime import datetime, timedelta
from django.utils import timezone


import os
#  = "https://seerbitapi.com/api/v2"  # or sandbox URL

# def get_encrypted_key():
#     payload = {"key": f"{settings.SEERBIT_SECRET_KEY}.{settings.SEERBIT_PUBLIC_KEY}"}
#     response = requests.post(f"https://seerbitapi.com/api/v2/encrypt/keys", json=payload, headers={"Content-Type": "application/json"})
#     data = response.json()

#     if response.status_code == 200 and data.get("status") == "SUCCESS":
#         return data["data"]["EncryptedSecKey"]["encryptedKey"]
#     raise Exception("Failed to get encrypted key from SeerBit")



# monnify/utils.py


def record_deposit(amount, description, timestamp):
    pass


def record_withdrawal(amount, description, timestamp):
    pass


class MonnifyClient:
    def __init__(self):
        self.base_url = settings.MONNIFY_BASE_URL
        self.api_key = settings.MONNIFY_API_KEY
        self.api_secret = settings.MONNIFY_API_SECRET
        self.contract_code = settings.MONNIFY_CONTRACT_CODE
        self.webhook_secret = settings.MONNIFY_WEBHOOK_SECRET

        # token and expiry
        self._access_token = None
        self._token_expires_at = None

    def _get_auth_header(self):
        """
        Return Basic authorization header for login.
        """
        creds = f"{self.api_key}:{self.api_secret}"
        b64 = base64.b64encode(creds.encode()).decode()
        # print(b64)
        return {"Authorization": f"Basic {b64}"}

    def get_access_token(self):
        """
        Authenticate with Monnify to get bearer access token (OAuth style).
        Cache it until it expires.
        """
        if self._access_token and timezone.now() < self._token_expires_at:
            return self._access_token

        url = f"{self.base_url}/api/v1/auth/login"
        headers = {"Content-Type": "application/json", **self._get_auth_header()}
        resp = requests.post(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        # print("RESPONSE: ")
        # print(data)
        body = data["responseBody"]
        token = body["accessToken"]
        expires_in = body["expiresIn"]  # seconds
        self._access_token = token
        self._token_expires_at = timezone.now() + timedelta(seconds=expires_in - 60)
        return token

    def _bearer_headers(self):
        token = self.get_access_token()
        # print(token)
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    # ----------------------------
    # PAYMENT / CHARGE / TRANSFER
    # ----------------------------

    def init_transaction(self, amount, customer_name, customer_email, payment_reference,
                         payment_description=None, redirect_url=None, payment_methods=None,
                         meta_data=None):
        """
        Initialize a transaction (for card + account transfer)  
        POST /api/v1/merchant/transactions/init-transaction
        """
        url = f"{self.base_url}/api/v1/merchant/transactions/init-transaction"
        payload = {
            "amount": amount,
            "customerName": customer_name,
            "customerEmail": customer_email,
            "paymentReference": payment_reference,
            "currencyCode": "NGN",
            "contractCode": self.contract_code,
        }
        if payment_description:
            payload["paymentDescription"] = payment_description
        if redirect_url:
            payload["redirectUrl"] = redirect_url
        if payment_methods:
            payload["paymentMethods"] = payment_methods
        if meta_data:
            payload["metaData"] = meta_data
        resp = requests.post(url, json=payload, headers=self._bearer_headers())
        # print(resp.json())
        resp.raise_for_status()
        return resp.json()

    def init_bank_transfer_payment(self, amount, customer_name, customer_email, payment_reference,
                                  payment_description=None, redirect_url=None, payment_methods=None,
                                  meta_data=None, bank_code=None):
        """
        First, initialize the transaction, then request Monnify to produce dynamic (virtual) account for bank transfer.
        """
        # Step 1: Initialize transaction
        init_resp = self.init_transaction(
            amount=amount,
            customer_name=customer_name,
            customer_email=customer_email if (customer_email) else os.getenv("DEFAULT_TRANSACTION_EMAIL"),
            payment_reference=payment_reference,
            payment_description=payment_description,
            redirect_url=redirect_url,
            payment_methods=payment_methods,
            meta_data=meta_data
        )

        transaction_reference = init_resp["responseBody"]["transactionReference"]

        # Step 2: Initialize bank transfer payment
        url = f"{self.base_url}/api/v1/merchant/bank-transfer/init-payment/"
        payload = {
            "transactionReference": transaction_reference
        }
        if bank_code:
            payload["bankCode"] = bank_code

        resp = requests.post(url, json=payload, headers=self._bearer_headers())
        resp.raise_for_status()
        return resp.json()

    def init_card_payment(self, amount, customer_name, customer_email, payment_reference,
                         payment_description=None, redirect_url=None, meta_data=None):
        """
        Initialize a transaction for card payment only.
        """
        payment_methods = ["CARD"]
        return self.init_transaction(
            amount=amount,
            customer_name=customer_name,
            customer_email=customer_email,
            payment_reference=payment_reference,
            payment_description=payment_description,
            redirect_url=redirect_url,
            payment_methods=payment_methods,
            meta_data=meta_data
        )
    
    # ---------------------------------------
    # DISBURSEMENTS / TRANSFERS (Settlement)
    # ---------------------------------------

    def initiate_single_transfer(self, beneficiary_account_name, beneficiary_bank_code,
                                 beneficiary_account_number, amount, narration,
                                 reference, callback_url=None):
        """
        Disburse to a single bank account  
        POST /api/v1/disbursement/single  
        (Monnify docs label “Initiate Transfer (Single)” under “Transfers / Disbursement”)  
        """
        url = f"{self.base_url}/api/v1/disbursement/single"
        payload = {
            "accountName": beneficiary_account_name,
            "accountNumber": beneficiary_account_number,
            "bankCode": beneficiary_bank_code,
            "amount": amount,
            "narration": narration,
            "reference": reference
        }
        if callback_url:
            payload["callbackUrl"] = callback_url

        resp = requests.post(url, json=payload, headers=self._bearer_headers())
        resp.raise_for_status()
        return resp.json()

    def initiate_bulk_transfer(self, transfers: list, bulk_reference, callback_url=None):
        """
        Bulk disbursements
        POST /api/v1/disbursement/bulk  
        'transfers' is list of dicts: each with accountName, accountNumber, bankCode, amount, narration, reference
        """
        url = f"{self.base_url}/api/v1/disbursement/bulk"
        payload = {
            "bulkReference": bulk_reference,
            "transfers": transfers
        }
        if callback_url:
            payload["callbackUrl"] = callback_url

        resp = requests.post(url, json=payload, headers=self._bearer_headers())
        resp.raise_for_status()
        return resp.json()

    # ----------------------------
    # STATUS / INQUIRY APIs
    # ----------------------------

    def get_transaction_status(self, transaction_reference):
        """
        GET /api/v2/transactions/{transactionReference}  
        """
        url = f"{self.base_url}/api/v2/transactions/{transaction_reference}"
        resp = requests.get(url, headers=self._bearer_headers())
        resp.raise_for_status()
        return resp.json()

    def get_single_transfer_status(self, reference):
        """
        GET /api/v1/disbursement/single/{reference}  
        """
        url = f"{self.base_url}/api/v1/disbursement/single/{reference}"
        resp = requests.get(url, headers=self._bearer_headers())
        resp.raise_for_status()
        return resp.json()

    def get_bulk_transfer_status(self, bulk_reference):
        """
        GET /api/v1/disbursement/bulk/{bulkReference}  
        """
        url = f"{self.base_url}/api/v1/disbursement/bulk/{bulk_reference}"
        resp = requests.get(url, headers=self._bearer_headers())
        resp.raise_for_status()
        return resp.json()

    # ----------------------------------
    # WEBHOOK / CALLBACK VERIFICATION
    # ----------------------------------

    def verify_webhook_signature(self, request_body: bytes, headers: dict) -> bool:
        """
        Verify Monnify webhook signature.
        - request_body: raw request body in bytes
        - headers: request headers (dict-like, case insensitive ideally)

        Monnify sends an HMAC SHA-512 signature of the raw request body,
        using your client secret as the key.
        The header name is 'Monnify-Signature'.
        """

        # Try both lowercase and proper-case header keys
        signature_header = headers.get("monnify-signature") or headers.get("Monnify-Signature")
        if not signature_header:
            return False

        # Compute hash with your client secret as key
        computed = hmac.new(
            key=self.api_secret.encode("utf-8"),
            msg=request_body,
            digestmod=hashlib.sha512
        ).hexdigest()

        # Strip "sha512=" prefix if present
        sig = signature_header
        if sig.startswith("sha512="):
            sig = sig.split("=", 1)[1]

        # Compare safely to avoid timing attacks
        return hmac.compare_digest(computed, sig)

    def handle_webhook_event(self, request_body: bytes, headers: dict):
        """
        Process a webhook from Monnify.
        Returns parsed JSON data if valid, or raise error.
        """
        if not self.verify_webhook_signature(request_body, headers):
            raise ValueError("Invalid webhook signature")

        payload = json.loads(request_body.decode())
        event_type = payload.get("eventType")
        event_data = payload.get("eventData")
        return event_type, event_data

    def get_reserved_account_reference(self, user_id):
        return f"USR-{user_id}"

    def get_reserved_account(self, user):
        """
        Get a Monnify reserved account with a given user.
        """
        headers = self._bearer_headers()

        # customer_email = user.email
        # customer_name = user.full_name
        account_reference = self.get_reserved_account_reference(user.id)

        # payload = {
        #     "accountReference": account_reference,
        #     "accountName": customer_name,
        #     "currencyCode": "NGN",
        #     "contractCode": self.contract_code,
        #     "customerEmail": customer_email,
        #     "customerName": customer_name,
        #     "getAllAvailableBanks": True,
        # }

        response = requests.get(
            f"{self.base_url}/api/v2/bank-transfer/reserved-accounts/{account_reference}",
            headers=headers,
            timeout=10
        )

        data = response.json()
        # print(data)
        if data.get("requestSuccessful"):
            return data['responseBody']

    def create_reserved_account(self, user):
        """
        Creates a Monnify reserved account for a verified user.
        """
        headers = self._bearer_headers()

        customer_email = user.email
        customer_name = user.full_name
        account_reference = self.get_reserved_account_reference(user.id)

        payload = {
            "accountReference": account_reference,
            "accountName": customer_name,
            "currencyCode": "NGN",
            "contractCode": self.contract_code,
            "customerEmail": customer_email,
            "customerName": customer_name,
            "getAllAvailableBanks": True,
        }

        response = requests.post(
            f"{self.base_url}/api/v2/bank-transfer/reserved-accounts/",
            json=payload,
            headers=headers,
            timeout=10
        )

        data = response.json()
        # print(data)
        if not data.get("requestSuccessful"):
            raise Exception(data.get("responseMessage", "Failed to create account"))

        return data["responseBody"]
    


class PaystackGateway:
    """
    Unified class for handling Paystack payment operations.
    Covers:
        - Virtual Dedicated Accounts (VDA)
        - Pay With Transfer (PWT) Account
        - Charge Initialization
        - Transfers (Payouts)
        - Transaction Verification
        - Webhook Signature Verification
    """

    def __init__(self, secret_key: str):
        if not secret_key:
            raise ValueError("Paystack secret key is required.")
        self.secret_key = secret_key
        self.base_url = "https://api.paystack.co"
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _post(self, endpoint: str, payload: dict) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, headers=self.headers, json=payload)
        data = response.json()
        if not response.ok or not data.get("status"):
            raise Exception(data.get("message", "Paystack request failed"))
        return data

    def _delete(self, endpoint: str) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        response = requests.delete(url, headers=self.headers)
        data = response.json()
        if not response.ok or not data.get("status"):
            raise Exception(data.get("message", "Paystack request failed"))
        return data

    def _get(self, endpoint: str) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=self.headers)
        data = response.json()
        if not response.ok or not data.get("status"):
            raise Exception(data.get("message", "Paystack request failed"))
        return data["data"]

    # ----------------------------------------
    # 1. CREATE DEDICATED VIRTUAL ACCOUNT (VDA)
    # ----------------------------------------
    def create_virtual_account(
        self,
        email: str,
        first_name: str,
        middle_name: str,
        last_name: str,
        phone: Optional[str] = None,
        preferred_bank: Optional[str] = "access-bank",
    ) -> Dict[str, Any]:
        payload = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "middle_name": middle_name,
            "phone": phone,
            "preferred_bank": preferred_bank,
            "country": "NG"
        }
        if phone:
            payload["phone"] = phone
        if preferred_bank:
            payload["preferred_bank"] = preferred_bank
        return self._post("/dedicated_account/assign", payload)


    def close_virtual_account(self, account_id: str) -> Dict[str, Any]:
        return self._delete("/dedicated_account/{account_id}")
    

    # ----------------------------------------
    # 2. PAY WITH TRANSFER (PWT) ACCOUNT
    # ----------------------------------------
    def generate_pwt_account(
        self,
        customer_email: str,
        amount: int,
        phone_number: str,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        Creates a temporary 'Pay With Transfer' account for a one-time transaction.
        Amount must be in kobo (e.g., 5000 NGN = 500000 kobo).
        """
        payload = {
            "amount": amount,
            "email": customer_email,
            "meta_data": {
                "phone_number": phone_number,
                "user_id": user_id,
            },
            "bank_transfer": {
                "account_expires_at": str(datetime.now() + timedelta(hours=48))
            } 
        }
        return self._post("/charge", payload)

    # ----------------------------------------
    # 3. INITIALIZE CHARGE (WITH PAYMENT METHODS)
    # ----------------------------------------
    def initialize_charge(
        self,
        email: str,
        amount: int,
        reference: Optional[str] = None,
        callback_url: Optional[str] = None,
        channels: Optional[list] = None,
        metadata: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """
        Initialize a charge with custom payment channels.
        Available channels: card, bank, ussd, mobile_money, qr, eft, etc.
        """
        payload = {
            "email": email,
            "amount": amount * 100,
        }
        if reference:
            payload["reference"] = reference
        if callback_url:
            payload["callback_url"] = callback_url
        if channels:
            payload["channels"] = channels
        if metadata:
            payload["metadata"] = metadata
        return self._post("/transaction/initialize", payload)

    # ----------------------------------------
    # 4. MAKE PAYOUT / TRANSFER
    # ----------------------------------------
    def make_payout(
        self,
        name: str,
        account_number: str,
        bank_code: str,
        amount: int,
        reason: Optional[str] = None,
        currency: str = "NGN",
    ) -> Dict[str, Any]:
        """
        Makes a payout to a recipient bank account.
        Amount is in kobo (e.g., 5000 NGN = 500000 kobo).
        """
        # Step 1: Create transfer recipient
        recipient_payload = {
            "type": "nuban",
            "name": name,
            "account_number": account_number,
            "bank_code": bank_code,
            "currency": currency,
        }
        recipient = self._post("/transferrecipient", recipient_payload)

        # Step 2: Initiate transfer
        transfer_payload = {
            "source": "balance",
            "amount": amount,
            "recipient": recipient["recipient_code"],
        }
        if reason:
            transfer_payload["reason"] = reason
        return self._post("/transfer", transfer_payload)

    # ----------------------------------------
    # 5. VERIFY TRANSACTION
    # ----------------------------------------
    def verify_transaction(self, reference: str) -> Dict[str, Any]:
        """
        Verify a transaction using its reference.
        """
        return self._get(f"/transaction/verify/{reference}")

    # ----------------------------------------
    # 6. VERIFY WEBHOOK SIGNATURE
    # ----------------------------------------
    def verify_webhook(self, raw_body: bytes, signature_header: str) -> bool:
        """
        Verify Paystack webhook using SHA512 HMAC signature.
        """
        computed = hmac.new(
            self.secret_key.encode("utf-8"), raw_body, hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(computed, signature_header)
