from .utils import PaystackGateway


class PaymentGatewayRouter:
    """
    Router to get the active Paystack gateway instance.
    """

    @staticmethod
    def get_active_gateway(purpose: str = "deposit") -> PaystackGateway:
        """
        Returns the PaystackGateway instance. Purpose param kept for API compatibility.
        """
        return PaystackGateway()
