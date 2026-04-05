from abc import ABC, abstractmethod

class VTUInterface(ABC):
    @abstractmethod
    def __init__(self, config=None):
        pass

    @abstractmethod
    def get_balance(self):
        pass

    @abstractmethod
    def get_available_services(self) -> list:
        """Returns a list of service types supported by this provider."""
        pass

    @abstractmethod
    def get_config_requirements(self) -> list:
        """Returns a list of dictionaries defining required config fields."""
        pass

    @abstractmethod
    def buy_airtime(self, network_id, amount, phone, request_id):
        pass

    @abstractmethod
    def buy_data(self, network_id, plan_id, phone, request_id):
        pass

    @abstractmethod
    def buy_tv(self, tv_id, package_id, smart_card_number, phone, request_id):
        pass

    @abstractmethod
    def buy_electricity(self, disco_id, plan_id, meter_number, phone, amount, request_id):
        pass
