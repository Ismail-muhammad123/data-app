from .models import PaymentGatewayConfig
from .utils import PaystackGatewayImpl, FlutterwaveGatewayImpl, MonnifyGatewayImpl
from .interfaces import BasePaymentGateway
from typing import Optional

class PaymentGatewayRouter:
    """
    Router to select and instantiate the active payment gateway.
    """

    @staticmethod
    def get_active_gateway(purpose: str = "deposit") -> Optional[BasePaymentGateway]:
        """
        Get the current active gateway for a specific purpose ('deposit' or 'withdrawal').
        """
        if purpose == "deposit":
            config = PaymentGatewayConfig.objects.filter(is_active=True, use_for_deposits=True).first()
        else:
            config = PaymentGatewayConfig.objects.filter(is_active=True, use_for_withdrawals=True).first()

        if not config:
            return None

        gateway_type = config.gateway
        conf = config.config_data

        if gateway_type == "paystack":
            return PaystackGatewayImpl(secret_key=conf.get("secret_key"))
        
        elif gateway_type == "flutterwave":
            return FlutterwaveGatewayImpl(secret_key=conf.get("secret_key"))
            
        elif gateway_type == "monnify":
            return MonnifyGatewayImpl(
                api_key=conf.get("api_key"),
                api_secret=conf.get("api_secret"),
                base_url=conf.get("base_url"),
                contract_code=conf.get("contract_code")
            )

        return None
