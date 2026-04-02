from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class BaseNotificationProvider(ABC):
    """
    Abstract interface for notification providers (Push, Email, SMS).
    """

    @abstractmethod
    def send(self, recipient: str, title: str, body: str, data: Optional[Dict[str, Any]] = None) -> bool:
        pass
