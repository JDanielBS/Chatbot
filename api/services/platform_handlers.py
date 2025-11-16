"""
Factory para obtener handlers de plataformas.
"""
from api.platforms.whatsapp.client import WhatsAppClient
from api.platforms.telegram.client import TelegramClient
from api.platforms.base import PlatformClient


def get_platform_client(platform: str) -> PlatformClient:
    """
    Obtiene un cliente para la plataforma especificada.
    
    Args:
        platform: Nombre de la plataforma (whatsapp, telegram)
        
    Returns:
        PlatformClient: Instancia del cliente de la plataforma
        
    Raises:
        ValueError: Si la plataforma no es soportada
    """
    platform_lower = platform.lower()
    
    if platform_lower == "whatsapp":
        return WhatsAppClient()
    elif platform_lower == "telegram":
        return TelegramClient()
    else:
        raise ValueError(f"Plataforma no soportada: {platform}")


def get_platform_handler(platform: str):
    """
    Alias para get_platform_client (compatibilidad).
    
    Args:
        platform: Nombre de la plataforma
        
    Returns:
        PlatformClient: Instancia del cliente
    """
    return get_platform_client(platform)


