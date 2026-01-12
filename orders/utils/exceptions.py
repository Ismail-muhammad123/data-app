class EBillsAPIError(Exception):
    """Base exception for eBills API"""


class AuthenticationError(EBillsAPIError):
    pass


class InsufficientBalanceError(EBillsAPIError):
    pass


class ValidationError(EBillsAPIError):
    pass
