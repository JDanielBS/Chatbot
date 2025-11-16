"""
Router de Telegram para integrar el bot con la API FastAPI.
Usa la nueva arquitectura de plataformas.
"""
import os
import logging
from fastapi import APIRouter, Request

from api.dependencies import get_timestamp
from api.services.message_service import process_message
from api.services.platform_handlers import get_platform_client
from api.config.messages import get_command_message
from api.utils.session_manager import get_all_sessions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["Telegram"])

# Configuración Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


@router.post("/webhook")
async def receive_message(request: Request):
    """
    Recibe y procesa mensajes de Telegram.
    
    Telegram envía un POST request con updates cuando se configura un webhook.
    """
    try:
        data = await request.json()
        logger.info(f"Webhook Telegram recibido: {data.get('update_id')}")
        
        # Obtener cliente de Telegram
        client = get_platform_client("telegram")
        
        # Extraer datos del mensaje usando el cliente
        message_data = client.extract_message_data(data)
        
        if not message_data:
            return {"status": "ok"}
        
        user_id = message_data['user_id']
        message_id = message_data.get('message_id')
        message_type = message_data.get('message_type', 'text')
        message_text = message_data.get('message_text')
        
        # Marcar como leído (Telegram no tiene esta funcionalidad, pero mantenemos la interfaz)
        if message_id:
            client.mark_as_read(message_id)
        
        # Procesar según el tipo de mensaje
        if message_type == 'text' and message_text:
            logger.info(f"📩 Mensaje Telegram de {user_id}: {message_text[:50]}")
            
            # Procesar mensaje (lógica común)
            response = await process_message(
                platform="telegram",
                user_id=user_id,
                message_text=message_text,
                message_id=message_id
            )
            
            # Enviar respuesta
            client.send_message(user_id, response)
        
        elif message_type in ['image', 'audio', 'video', 'document']:
            # Mensajes no soportados
            response = get_command_message(f"{message_type}_received")
            if not response:
                response = get_command_message("image_received")  # Fallback
            client.send_message(user_id, response)
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Error procesando webhook Telegram: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.get("/webhook")
async def set_webhook():
    """
    Endpoint para configurar el webhook de Telegram.
    
    Nota: Normalmente se hace manualmente con:
    https://api.telegram.org/bot{TOKEN}/setWebhook?url={YOUR_URL}/telegram/webhook
    """
    return {
        "message": "Para configurar el webhook, usa:",
        "url": f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url=TU_URL/telegram/webhook",
        "status": "ok"
    }


@router.get("/health")
async def telegram_health():
    """
    Health check del servicio de Telegram.
    """
    all_sessions = get_all_sessions()
    telegram_sessions = {
        k: v for k, v in all_sessions.items() 
        if v.get('platform') == 'telegram'
    }
    
    return {
        "status": "ok",
        "telegram_configured": bool(TELEGRAM_BOT_TOKEN),
        "active_sessions": len(telegram_sessions),
        "timestamp": get_timestamp()
    }


