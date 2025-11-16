"""
Cliente de Telegram Bot API.
Implementa la interfaz PlatformClient.
"""
import os
import logging
import requests
from typing import Dict, Optional

from api.platforms.base import PlatformClient

logger = logging.getLogger(__name__)


class TelegramClient(PlatformClient):
    """
    Cliente para interactuar con Telegram Bot API.
    """
    
    def __init__(self, bot_token: str = None):
        """
        Inicializa el cliente de Telegram.
        
        Args:
            bot_token: Token del bot de Telegram (si no se proporciona, se lee de .env)
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN no configurado")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, user_id: str, message: str) -> bool:
        """
        Envía un mensaje de texto a Telegram.
        
        Args:
            user_id: Chat ID del usuario
            message: Texto del mensaje
            
        Returns:
            bool: True si se envió exitosamente
        """
        if not self.bot_token:
            logger.error("Telegram bot token no configurado")
            return False
        
        url = f"{self.api_url}/sendMessage"
        
        data = {
            "chat_id": user_id,
            "text": message,
            "parse_mode": "Markdown"  # Soporta Markdown básico
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info(f"Mensaje Telegram enviado a {user_id}")
                    return True
                else:
                    logger.error(f"Error Telegram API: {result.get('description')}")
                    return False
            else:
                logger.error(f"Error HTTP al enviar mensaje Telegram: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error en send_message Telegram: {str(e)}")
            return False
    
    def mark_as_read(self, message_id: str) -> None:
        """
        Marca un mensaje como leído en Telegram.
        
        Nota: Telegram no tiene una API nativa para "marcar como leído"
        como WhatsApp. Este método está aquí para mantener la interfaz,
        pero no hace nada.
        
        Args:
            message_id: ID del mensaje (no usado en Telegram)
        """
        # Telegram no tiene "marcar como leído" en su API
        # Podríamos usar "answerCallbackQuery" para botones, pero no para mensajes normales
        pass
    
    def extract_message_data(self, webhook_data: dict) -> Optional[Dict]:
        """
        Extrae datos del mensaje del webhook de Telegram.
        
        Args:
            webhook_data: Datos crudos del webhook de Telegram (update)
            
        Returns:
            dict con keys: 'user_id', 'message_text', 'message_id', 'message_type'
            o None si no hay mensaje válido
        """
        try:
            # Telegram envía updates con estructura diferente
            if 'message' in webhook_data:
                message = webhook_data['message']
                chat = message.get('chat', {})
                chat_id = str(chat.get('id'))
                message_id = message.get('message_id')
                
                # Verificar si es texto
                if 'text' in message:
                    return {
                        'user_id': chat_id,
                        'message_text': message.get('text', ''),
                        'message_id': message_id,
                        'message_type': 'text'
                    }
                # Otros tipos de mensaje
                elif 'photo' in message:
                    return {
                        'user_id': chat_id,
                        'message_text': None,
                        'message_id': message_id,
                        'message_type': 'image'
                    }
                elif 'video' in message:
                    return {
                        'user_id': chat_id,
                        'message_text': None,
                        'message_id': message_id,
                        'message_type': 'video'
                    }
                elif 'document' in message:
                    return {
                        'user_id': chat_id,
                        'message_text': None,
                        'message_id': message_id,
                        'message_type': 'document'
                    }
                elif 'voice' in message or 'audio' in message:
                    return {
                        'user_id': chat_id,
                        'message_text': None,
                        'message_id': message_id,
                        'message_type': 'audio'
                    }
            
            return None
        except Exception as e:
            logger.error(f"Error extrayendo datos de Telegram: {e}")
            return None
    
    def get_platform_name(self) -> str:
        """Retorna el nombre de la plataforma."""
        return "telegram"


