from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseVTUProvider(ABC):
    """
    Abstract interface for all VTU providers.
    """

    

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def buy_airtime(self, phone: str, network: str, amount: float, reference: str) -> Dict[str, Any]:
        """
        Buy airtime.
        Returns: {'status': SUCCESS/FAILED/PENDING, 'provider_reference': '...', 'raw_response': {...}}
        """
        pass

    @abstractmethod
    def buy_data(self, phone: str, network: str, plan_id: str, amount: float, reference: str) -> Dict[str, Any]:
        """
        Buy data plans.
        """
        pass

    @abstractmethod
    def pay_bill(self, service_type: str, identifier: str, amount: float, plan_id: str, reference: str, metadata: dict = None) -> Dict[str, Any]:
        """
        Generic bill payment (CableTV, Electricity, Education).
        """
        pass

    @abstractmethod
    def query_transaction(self, reference: str) -> Dict[str, Any]:
        """
        Check the status of a VTU transaction.
        """
        pass

    @abstractmethod
    def validate_meter(self, meter_number: str, service: str) -> Dict[str, Any]:
        """
        Validate electricity meter before payment.
        """
        pass

    @abstractmethod
    def validate_cable_id(self, card_number: str, service: str) -> Dict[str, Any]:
        """
        Validate smartcard number for Cable TV.
        """
        pass

    @abstractmethod
    def get_wallet_balance(self) -> float:
        """
        Get the balance of the platform's wallet with this provider.
        """
        pass

    @abstractmethod
    def get_available_services(self) -> List[Dict[str, Any]]:
        """
        Get all services/networks and plans available on this provider.
        """
        pass

    @abstractmethod
    def get_airtime_networks(self) -> List[Dict[str, Any]]:
        """
        Fetch available airtime networks from the provider API.
        """
        pass

    @abstractmethod
    def get_data_plans(self, network_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch available data plans/variations from the provider API.
        """
        pass

    @abstractmethod
    def get_cable_tv_packages(self, service_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch available Cable TV packages from the provider API.
        """
        pass

    @abstractmethod
    def get_electricity_services(self) -> List[Dict[str, Any]]:
        """
        Fetch available electricity services/discos from the provider API.
        """
        pass

    @abstractmethod
    def get_internet_packages(self) -> List[Dict[str, Any]]:
        """
        Fetch available Internet variations from the provider API.
        """
        pass

    @abstractmethod
    def get_education_services(self) -> List[Dict[str, Any]]:
        """
        Fetch available education services/variations from the provider API.
        """
        pass
