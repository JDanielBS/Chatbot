from api.platforms.whatsapp.client import WhatsAppClient
from api.platforms.telegram.client import TelegramClient
from api.platforms.base import PlatformClient


def get_platform_client(platform: str) -> PlatformClient:
    platform_lower = platform.lower()
    
    if platform_lower == "whatsapp":
        return WhatsAppClient()
    elif platform_lower == "telegram":
        return TelegramClient()
    else:
        raise ValueError(f"Plataforma no soportada: {platform}")

