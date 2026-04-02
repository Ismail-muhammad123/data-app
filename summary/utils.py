import requests
from django.conf import settings
from orders.services.clubkonnect import ClubKonnectClient
from payments.utils import PaystackGateway
from config.utils import TermiiClient

def get_api_wallet_balance():
    client = ClubKonnectClient()
    balance = client.get_balance()
  
    if balance and isinstance(balance, dict):
        try:
            balance_amount = balance.get("balance", 0)
            balance_amount = float(str(balance_amount).replace(',', ''))
            return balance_amount
        except (TypeError, ValueError):
            return 0.0
    
    return 0.0

def get_paystack_balance():
    secret_key = settings.PAYSTACK_SECRET_KEY
    if not secret_key:
        return 0.0
    
    gateway = PaystackGateway(secret_key)
    try:
        url = f"{gateway.base_url}/balance"
        headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers)
        if response.ok:
            data = response.json().get("data", [])
            for item in data:
                if item.get("currency") == "NGN":
                    return float(item.get("balance", 0)) / 100
        return 0.0
    except Exception:
        return 0.0

def get_termii_balance():
    if not settings.TERMII_API_KEY:
        return 0.0
    
    client = TermiiClient(settings.TERMII_API_KEY, settings.TERMII_SENDER_ID)
    try:
        data = client.get_balance()
        if "balance" in data:
            return float(data["balance"])
        return 0.0
    except Exception:
        return 0.0
