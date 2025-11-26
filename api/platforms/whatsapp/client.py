import os
import logging
import requests
import json
from typing import Dict, Optional

from api.platforms.base import PlatformClient

logger = logging.getLogger(__name__)


class WhatsAppClient(PlatformClient):
    
    def __init__(self):
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.api_url = f'https://graph.facebook.com/v22.0/{self.phone_number_id}'
        
        # Log de configuración
        if self.access_token:
            token_preview = f"{self.access_token[:15]}...{self.access_token[-5:]}" if len(self.access_token) > 20 else "***"
            logger.info(f"📱 WhatsApp Access Token configurado: {token_preview}")
        else:
            logger.warning("⚠️ WHATSAPP_ACCESS_TOKEN no configurado")
            
        if self.phone_number_id:
            logger.info(f"📱 WhatsApp Phone Number ID: {self.phone_number_id}")
        else:
            logger.warning("⚠️ WHATSAPP_PHONE_NUMBER_ID no configurado")
    
    def send_message(self, user_id: str, message: str) -> bool:
        logger.info(f"📤 [WHATSAPP] Intentando enviar mensaje...")
        logger.info(f"   → to (user_id): {user_id}")
        logger.info(f"   → mensaje (primeros 100 chars): {message[:100] if message else 'VACÍO'}...")
        logger.info(f"   → longitud mensaje: {len(message) if message else 0} caracteres")
        
        if not self.access_token:
            logger.error("❌ [WHATSAPP] Access Token NO configurado")
            return False
            
        if not self.phone_number_id:
            logger.error("❌ [WHATSAPP] Phone Number ID NO configurado")
            return False
        
        if not message or len(message.strip()) == 0:
            logger.error("❌ [WHATSAPP] Mensaje vacío, no se puede enviar")
            return False
        
        url = f'{self.api_url}/messages'
        logger.info(f"   → URL: {url}")
        
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
        
        logger.info(f"   → Payload: {json.dumps(data, ensure_ascii=False)[:300]}...")
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            logger.info(f"   → Status Code: {response.status_code}")
            
            try:
                response_json = response.json()
                logger.info(f"   → Response JSON: {json.dumps(response_json, ensure_ascii=False)}")
            except:
                logger.info(f"   → Response Text: {response.text[:500]}")
            
            if response.status_code == 200:
                logger.info(f"✅ [WHATSAPP] Mensaje enviado exitosamente a {user_id}")
                return True
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Sin mensaje')
                    error_code = error_data.get('error', {}).get('code', 'Sin código')
                    error_subcode = error_data.get('error', {}).get('error_subcode', 'N/A')
                    logger.error(f"❌ [WHATSAPP] API Error {error_code} (subcode: {error_subcode}): {error_msg}")
                except:
                    logger.error(f"❌ [WHATSAPP] Error HTTP {response.status_code}: {response.text[:300]}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ [WHATSAPP] Timeout al enviar mensaje")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ [WHATSAPP] Error de conexión: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ [WHATSAPP] Error inesperado: {type(e).__name__}: {str(e)}")
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


