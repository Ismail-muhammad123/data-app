# payments/seerbit.py
import base64
import requests
from django.conf import settings

from seerbit.client import Client
from seerbit.enums import EnvironmentEnum

from seerbit.seerbitlib import SeerBit
from seerbit.service.authentication import Authentication
from seerbit.service.card_service import CardService

client = Client()


def authenticate() -> str:
    """ User authentication token """
    print("================== start authentication ==================")
    client.api_base = SeerBit.TEST_API_BASE
    client.environment = EnvironmentEnum.LIVE.value
    client.private_key =settings.SEERBIT_SECRET_KEY  
    client.public_key = settings.SEERBIT_PUBLIC_KEY
    client.timeout = 20
    auth_service = Authentication(client)
    auth_service.auth()
    print("================== stop authentication ==================")
    return auth_service.get_token()


def card_authorize(token_str, payment_ref, amount, full_name, email, phone, card_number, card_expiry_month, card_expiry_year, cvv, pin):
    """ Initiate Card Payment """
    print("================== start card authorize ==================")
    # random_number = randint(10000000, 99999999)
    # payment_ref = "SBT_" + str(random_number)
    card_payload = {
        "publicKey": client.public_key,
        "amount": amount,
        "fee": "0",
        "fullName": full_name,
        "mobileNumber": phone,
        "currency": "NGN",
        "country": "NG",
        "paymentReference": payment_ref,
        "email": email,
        # "productId": "product101",
        # "productDescription": "ONE WORLD",
        # "clientAppCode": "kpp64",
        "redirectUrl": "http://z9trade.com/payment/verifiy",
        "paymentType": "CARD",
        "scheduleId": "",
        # "channelType": "Mastercard",
        # "deviceType": "Apple Laptop",
        # "sourceIP": "127.0.0.1:3456",
        "cardNumber": card_number,
        "cvv": cvv,
        "expiryMonth": card_expiry_month,
        "expiryYear": card_expiry_year,
        "pin": pin,
        # "type": "3DSECURE",
        "retry": "false",
        # "invoiceNumber": "1234567890abc123ac"
    }
    card_service = CardService(client, token_str)
    json_response = card_service.authorize(card_payload)
    print("================== stop card authorize ==================")
    return json_response





# -------------------------------------------------------------------------------------------------------

# class SeerbitClient:
#     def __init__(self):
#         self.base = getattr(settings, "SEERBIT_BASE_URL", "https://seerbitapi.com/api/v2").rstrip("/")
#         self.pub = settings.SEERBIT_PUBLIC_KEY
#         self.sec = settings.SEERBIT_SECRET_KEY
#         self.enc_key_cache = getattr(settings, "SEERBIT_ENCRYPTED_KEY_CACHE_KEY", "seerbit_encrypted_key")
#         self.enc_ttl = getattr(settings, "SEERBIT_ENCRYPTED_KEY_TTL", 9 * 60)

#     # def _basic_headers(self):
#     #     basic = base64.b64encode(f"{self.pub}:{self.sec}".encode()).decode()
#     #     return {"Authorization": f"Bearer {basic}", "Content-Type": "application/json"}

#     def _get_encrypted_key(self):
#         token = cache.get(self.enc_key_cache)
#         if token:
#             return token
#         url = f"{self.base}/encrypt/keys"
#         payload = {"key": f"{self.sec}.{self.pub}"}
#         r = requests.post(url, json=payload, timeout=30)
#         r.raise_for_status()
#         data = r.json()
#         # path per docs (may vary); adapt if response shape differs
#         encrypted = data["data"]["EncryptedSecKey"]["encryptedKey"]
#         cache.set(self.enc_key_cache, encrypted, self.enc_ttl)
#         return encrypted

#     def _bearer_headers(self):
#         return {
#             "Authorization": f"Bearer {self._get_encrypted_key()}",
        
#             "Content-Type": "application/json",
#         }

#     def tokenize_card(self, payload: dict):
#         url = f"{self.base}/payments/create-token"
#         r = requests.post(url, json=payload, headers=self._bearer_headers(), timeout=45)
#         print("STATUS CODE: ", r.status_code)
#         print("RESPONSE: ", r.json())
#         r.raise_for_status()
#         return r.json()

#     def authorise_with_token(self, payload: dict):
#         url = f"{self.base}/payments/authorise"
#         r = requests.post(url, json=payload, headers=self._bearer_headers(), timeout=45)
#         r.raise_for_status()
#         return r.json()

#     def charge_token(self, payload: dict):
#         url = f"{self.base}/payments/charge-token"
#         r = requests.post(url, json=payload, headers=self._bearer_headers(), timeout=45)
#         r.raise_for_status()
#         return r.json()

#     def verify(self, payment_reference: str):
#         url = f"https://seerbitapi.com/api/v3/payments/query/{payment_reference}"
#         r = requests.get(url, headers=self._bearer_headers(), timeout=30)
#         r.raise_for_status()
#         return r.json()
