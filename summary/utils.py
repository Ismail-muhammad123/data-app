import requests
from django.conf import settings
from orders.services.clubkonnect import ClubKonnectClient
from payments.utils import PaystackGateway
from config.utils import TermiiClient

def get_api_wallet_balance():
    from orders.services.clubkonnect import ClubKonnectClient
    try:
        client = ClubKonnectClient()
        balance = client.get_balance()
      
        if balance and isinstance(balance, dict):
            balance_amount = balance.get("balance", 0)
            balance_amount = float(str(balance_amount).replace(',', ''))
            return balance_amount
    except Exception:
        return 0.0
    
    return 0.0

def get_paystack_balance():
    from payments.models import PaymentGatewayConfig
    config = PaymentGatewayConfig.objects.filter(name='paystack', is_active=True).first()
    secret_key = config.secret_key if config else getattr(settings, 'PAYSTACK_SECRET_KEY', None)
    
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
    from notifications.models import NotificationProviderConfig
    config = NotificationProviderConfig.objects.filter(provider_type='sms', is_active=True).first()
    api_key = config.config_data.get('api_key') if config else getattr(settings, 'TERMII_API_KEY', None)
    sender_id = config.config_data.get('sender_id') if config else getattr(settings, 'TERMII_SENDER_ID', None)

    if not api_key:
        return 0.0
    
    client = TermiiClient(api_key, sender_id)
    try:
        data = client.get_balance()
        if data and "balance" in data:
            return float(data["balance"])
        return 0.0
    except Exception:
        return 0.0
