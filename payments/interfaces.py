from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class BasePaymentGateway(ABC):
    """
    Abstract interface for all payment gateways (Paystack, Flutterwave, Monnify, etc.)
    """

    @abstractmethod
    def initialize_deposit(
        self, 
        email: str, 
        amount: float, 
        reference: str, 
        callback_url: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Dict[str, Any]:
        """
        Initialize a checkout / charge. 
        Returns dict with keys: 'status', 'checkout_url', 'reference', 'raw_response'
        """
        pass

    @abstractmethod
    def verify_transaction(self, reference: str) -> Dict[str, Any]:
        """
        Verify the status of a transaction.
        Returns dict with keys: 'status' (SUCCESS, FAILED, PENDING), 'amount', 'currency', 'raw_response'
        """
        pass

    @abstractmethod
    def list_banks(self) -> List[Dict[str, str]]:
        """
        List supported banks for transfers.
        Returns list of dicts: [{'name': 'Bank X', 'code': '011'}, ...]
        """
        pass

    @abstractmethod
    def resolve_account(self, account_number: str, bank_code: str) -> Dict[str, Any]:
        """
        Resolve bank account number to account name.
        Returns dict with keys: 'account_name', 'account_number', 'bank_code'
        """
        pass

    @abstractmethod
    def initiate_transfer(
        self,
        amount: float,
        bank_code: str,
        account_number: str,
        account_name: str,
        reference: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send money from the platform to a user's bank account.
        Returns dict with keys: 'status' (SUCCESS, FAILED, PENDING), 'transfer_code', 'raw_response'
        """
        pass

    @abstractmethod
    def verify_webhook(self, raw_body: bytes, signature: str) -> bool:
        """
        Verify that a webhook request is authentic.
        """
        pass
