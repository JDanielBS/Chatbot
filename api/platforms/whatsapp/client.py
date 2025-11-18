import os
import logging
import requests
from typing import Dict, Optional

from api.platforms.base import PlatformClient

logger = logging.getLogger(__name__)


class WhatsAppClient(PlatformClient):
    
    def __init__(self):
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.api_url = f'https://graph.facebook.com/v22.0/{self.phone_number_id}'
    
    def send_message(self, user_id: str, message: str) -> bool:
        if not self.access_token or not self.phone_number_id:
            logger.error("WhatsApp credentials no configuradas")
            return False
        
        url = f'{self.api_url}/messages'
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": user_id,
            "type": "text",
            "text": {"body": message}
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                logger.info(f"Mensaje WhatsApp enviado a {user_id}")
                return True
            else:
                logger.error(f"Error al enviar mensaje WhatsApp: {response.json()}")
                return False
        except Exception as e:
            logger.error(f"Error en send_message WhatsApp: {str(e)}")
            return False
    
    def mark_as_read(self, message_id: str) -> None:
        if not self.access_token or not self.phone_number_id:
            return
        
        url = f'{self.api_url}/messages'
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            requests.post(url, headers=headers, json=data, timeout=5)
        except Exception as e:
            logger.error(f"Error al marcar como leído WhatsApp: {str(e)}")
    
    def extract_message_data(self, webhook_data: dict) -> Optional[Dict]:
        try:
            if 'entry' not in webhook_data:
                return None
            
            for entry in webhook_data.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    
                    if 'messages' in value:
                        for message in value['messages']:
                            user_id = message.get('from')
                            message_id = message.get('id')
                            message_type = message.get('type')
                            
                            if message_type == 'text':
                                message_text = message.get('text', {}).get('body', '')
                                return {
                                    'user_id': user_id,
                                    'message_text': message_text,
                                    'message_id': message_id,
                                    'message_type': message_type
                                }
                            elif message_type in ['image', 'audio', 'video', 'document']:
                                return {
                                    'user_id': user_id,
                                    'message_text': None,
                                    'message_id': message_id,
                                    'message_type': message_type
                                }
            
            return None
        except Exception as e:
            logger.error(f"Error extrayendo datos de WhatsApp: {e}")
            return None
    
    def get_platform_name(self) -> str:
        return "whatsapp"


