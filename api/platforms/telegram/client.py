import os
import logging
import requests
from typing import Dict, Optional

from api.platforms.base import PlatformClient

logger = logging.getLogger(__name__)


class TelegramClient(PlatformClient):
    
    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN no configurado")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, user_id: str, message: str) -> bool:
        if not self.bot_token:
            logger.error("Telegram bot token no configurado")
            return False
        
        url = f"{self.api_url}/sendMessage"
        
        data = {
            "chat_id": user_id,
            "text": message,
            "parse_mode": "Markdown"  
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
    
    def extract_message_data(self, webhook_data: dict) -> Optional[Dict]:
        try:
            if 'message' in webhook_data:
                message = webhook_data['message']
                chat = message.get('chat', {})
                chat_id = str(chat.get('id'))
                message_id = message.get('message_id')
                
                if 'text' in message:
                    return {
                        'user_id': chat_id,
                        'message_text': message.get('text', ''),
                        'message_id': message_id,
                        'message_type': 'text'
                    }
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
        return "telegram"


