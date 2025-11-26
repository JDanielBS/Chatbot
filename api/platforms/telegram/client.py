import os
import logging
import requests
import json
from typing import Dict, Optional

from api.platforms.base import PlatformClient

logger = logging.getLogger(__name__)

class TelegramClient(PlatformClient):
    
    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN no configurado")
        else:
            # Mostrar solo los primeros y últimos caracteres del token
            token_preview = f"{self.bot_token[:10]}...{self.bot_token[-5:]}" if len(self.bot_token) > 15 else "***"
            logger.info(f"🤖 Telegram Bot Token configurado: {token_preview}")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, user_id: str, message: str) -> bool:
        logger.info(f"📤 [TELEGRAM] Intentando enviar mensaje...")
        logger.info(f"   → chat_id: {user_id}")
        logger.info(f"   → mensaje (primeros 100 chars): {message[:100] if message else 'VACÍO'}...")
        logger.info(f"   → longitud mensaje: {len(message) if message else 0} caracteres")
        
        if not self.bot_token:
            logger.error("❌ [TELEGRAM] Bot token NO configurado")
            return False
        
        if not message or len(message.strip()) == 0:
            logger.error("❌ [TELEGRAM] Mensaje vacío, no se puede enviar")
            return False
        
        url = f"{self.api_url}/sendMessage"
        logger.info(f"   → URL: {url[:50]}...")
        
        # Primero intentar sin parse_mode por si hay problemas con Markdown
        data = {
            "chat_id": user_id,
            "text": message,
            "parse_mode": "Markdown"  
        }
        
        logger.info(f"   → Payload: {json.dumps(data, ensure_ascii=False)[:200]}...")
        
        try:
            response = requests.post(url, json=data, timeout=10)
            logger.info(f"   → Status Code: {response.status_code}")
            
            try:
                response_json = response.json()
                logger.info(f"   → Response JSON: {json.dumps(response_json, ensure_ascii=False)}")
            except:
                logger.info(f"   → Response Text: {response.text[:500]}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info(f"✅ [TELEGRAM] Mensaje enviado exitosamente a {user_id}")
                    return True
                else:
                    error_desc = result.get('description', 'Sin descripción')
                    error_code = result.get('error_code', 'Sin código')
                    logger.error(f"❌ [TELEGRAM] API Error: {error_code} - {error_desc}")
                    return False
            else:
                # Si falla con Markdown, intentar sin parse_mode
                logger.warning(f"⚠️ [TELEGRAM] Error {response.status_code}, reintentando sin Markdown...")
                data_plain = {
                    "chat_id": user_id,
                    "text": message
                }
                response_retry = requests.post(url, json=data_plain, timeout=10)
                logger.info(f"   → Retry Status: {response_retry.status_code}")
                
                try:
                    retry_json = response_retry.json()
                    logger.info(f"   → Retry Response: {json.dumps(retry_json, ensure_ascii=False)}")
                    
                    if response_retry.status_code == 200 and retry_json.get('ok'):
                        logger.info(f"✅ [TELEGRAM] Mensaje enviado (sin Markdown) a {user_id}")
                        return True
                except:
                    logger.error(f"   → Retry Response Text: {response_retry.text[:500]}")
                
                logger.error(f"❌ [TELEGRAM] Error HTTP: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ [TELEGRAM] Timeout al enviar mensaje")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ [TELEGRAM] Error de conexión: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ [TELEGRAM] Error inesperado: {type(e).__name__}: {str(e)}")
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


