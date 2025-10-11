
import requests
from django.conf import settings

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

import base64
import hashlib
import hmac
import json
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone

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
        print(resp.json())
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
        url = f"{self.base_url}/api/v1/merchant/bank-transfer/init-payment"
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
    
    # ----------------------------
    # DISBURSEMENTS / TRANSFERS (Settlement)
    # ----------------------------

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

    # ----------------------------
    # WEBHOOK / CALLBACK VERIFICATION
    # ----------------------------

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
