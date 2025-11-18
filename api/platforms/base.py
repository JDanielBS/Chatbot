from abc import ABC, abstractmethod
from typing import Dict, Optional


class PlatformClient(ABC):
    
    @abstractmethod
    def send_message(self, user_id: str, message: str) -> bool:
        pass
    
    @abstractmethod
    def extract_message_data(self, webhook_data: dict) -> Optional[Dict]:
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        pass


