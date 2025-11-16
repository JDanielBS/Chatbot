"""
Utilidades para WhatsApp: hash, sesiones, envío de mensajes.
"""
import os
import hashlib
import logging
import requests
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)

WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')

whatsapp_sessions: Dict[str, Dict] = {}


def hash_phone_number(phone_number: str) -> str:
    """
    Genera un hash anonimizado del número de teléfono.
    
    Args:
        phone_number: Número de teléfono en formato internacional
        
    Returns:
        str: Hash SHA256 del número (primeros 16 caracteres)
    """
    return hashlib.sha256(phone_number.encode()).hexdigest()[:16]


def get_session(phone_number: str) -> Dict:
    """
    Obtiene o crea una sesión para un número de teléfono.
    
    Args:
        phone_number: Número de teléfono
        
    Returns:
        dict: Información de la sesión
    """
    phone_hash = hash_phone_number(phone_number)
    
    if phone_hash not in whatsapp_sessions:
        whatsapp_sessions[phone_hash] = {
            'opt_in': False,
            'mode': 'extended',
            'thread_id': f"whatsapp_{phone_hash}",
            'first_interaction': datetime.now().isoformat()
        }
    
    return whatsapp_sessions[phone_hash]


def send_whatsapp_message(phone_number: str, message: str) -> bool:
    """
    Envía un mensaje de texto a WhatsApp.
    
    Args:
        phone_number: Número de destino
        message: Texto del mensaje
        
    Returns:
        bool: True si se envió exitosamente
    """
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.error("WhatsApp credentials no configuradas")
        return False
    
    url = f'https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_NUMBER_ID}/messages'
    
    headers = {
        'Authorization': f'Bearer {WHATSAPP_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": message}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            logger.info(f"Mensaje enviado a {phone_number}")
            return True
        else:
            logger.error(f"Error al enviar mensaje: {response.json()}")
            return False
    except Exception as e:
        logger.error(f"Error en send_whatsapp_message: {str(e)}")
        return False


def mark_message_as_read(message_id: str) -> None:
    """
    Marca un mensaje como leído.
    
    Args:
        message_id: ID del mensaje de WhatsApp
    """
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        return
    
    url = f'https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_NUMBER_ID}/messages'
    
    headers = {
        'Authorization': f'Bearer {WHATSAPP_ACCESS_TOKEN}',
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
        logger.error(f"Error al marcar como leído: {str(e)}")

