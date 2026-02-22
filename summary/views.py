from orders.services.clubkonnect import ClubKonnectClient
from payments.utils import PaystackGateway
from django.conf import settings

def get_api_wallet_balance():
    client = ClubKonnectClient()
    balance = client.get_balance()

    if balance and isinstance(balance, dict):
        balance_amount = balance.get("balance", 0)
        balance_amount = float(balance_amount.replace(',', ''))
        try:
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
        # gateway.get_balance() now returns a formatted string like "NGN 1,000.00"
        # I need the float value for calculations. 
        # Actually, let me modify PaystackGateway or just parse it here.
        # Let's check PaystackGateway._get("/balance") again.
        
        # Original get_balance in PaystackGateway:
        # for item in balance_data:
        #     if item.get("currency") == "NGN":
        #         balance = float(item.get("balance", 0)) / 100
        #         return f"NGN {balance:,.2f}"
        
        # I'll add a get_balance_float method to PaystackGateway or just re-implement it here.
        url = f"{gateway.base_url}/balance"
        response = requests.get(url, headers=gateway.headers)
        if response.ok:
            data = response.json().get("data", [])
            for item in data:
                if item.get("currency") == "NGN":
                    return float(item.get("balance", 0)) / 100
        return 0.0
    except Exception:
        return 0.0

# I need requests in summary/views.py for the re-implementation
import requests
