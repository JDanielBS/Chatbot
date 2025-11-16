"""
Clase base abstracta para todas las plataformas de mensajería.
Define la interfaz común que deben implementar todas las plataformas.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional


class PlatformClient(ABC):
    """
    Clase base abstracta para clientes de plataformas de mensajería.
    
    Todas las plataformas (WhatsApp, Telegram, etc.) deben implementar
    estos métodos para mantener una interfaz consistente.
    """
    
    @abstractmethod
    def send_message(self, user_id: str, message: str) -> bool:
        """
        Envía un mensaje de texto al usuario.
        
        Args:
            user_id: Identificador único del usuario en la plataforma
            message: Texto del mensaje a enviar
            
        Returns:
            bool: True si se envió exitosamente, False en caso contrario
        """
        pass
    
    @abstractmethod
    def mark_as_read(self, message_id: str) -> None:
        """
        Marca un mensaje como leído (si la plataforma lo soporta).
        
        Args:
            message_id: ID del mensaje a marcar como leído
        """
        pass
    
    @abstractmethod
    def extract_message_data(self, webhook_data: dict) -> Optional[Dict]:
        """
        Extrae los datos del mensaje del formato del webhook de la plataforma.
        
        Args:
            webhook_data: Datos crudos del webhook
            
        Returns:
            dict con keys: 'user_id', 'message_text', 'message_id', 'message_type'
            o None si no hay mensaje válido
        """
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Retorna el nombre de la plataforma.
        
        Returns:
            str: Nombre de la plataforma (ej: "whatsapp", "telegram")
        """
        pass


