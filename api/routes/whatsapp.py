"""
Router de WhatsApp para integrar el bot con la API FastAPI.
Usa la nueva arquitectura de plataformas.
"""
import os
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse

from api.dependencies import get_timestamp
from api.services.message_service import process_message
from api.services.platform_handlers import get_platform_client
from api.config.messages import get_command_message
from api.utils.session_manager import get_all_sessions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

# Configuración WhatsApp
WEBHOOK_VERIFY_TOKEN = os.getenv('WEBHOOK_VERIFY_TOKEN')
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')


@router.get("/webhook")
async def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge")
):
    """
    Verifica el webhook de Meta (WhatsApp).
    
    Meta envía un GET request con estos parámetros para verificar el webhook.
    """
    if hub_mode == 'subscribe' and hub_verify_token == WEBHOOK_VERIFY_TOKEN:
        logger.info("✓ Webhook verificado correctamente")
        return PlainTextResponse(hub_challenge, status_code=200)
    else:
        logger.error("✗ Verificación de webhook fallida")
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/webhook")
async def receive_message(request: Request):
    """
    Recibe y procesa mensajes de WhatsApp.
    
    Meta envía un POST request con los mensajes recibidos.
    """
    try:
        data = await request.json()
        logger.info(f"Webhook WhatsApp recibido: {data.get('entry', [])}")
        
        # Obtener cliente de WhatsApp
        client = get_platform_client("whatsapp")
        
        # Extraer datos del mensaje usando el cliente
        message_data = client.extract_message_data(data)
        
        if not message_data:
            return {"status": "ok"}
        
        user_id = message_data['user_id']
        message_id = message_data.get('message_id')
        message_type = message_data.get('message_type', 'text')
        message_text = message_data.get('message_text')
        
        # Marcar como leído (si aplica)
        if message_id:
            client.mark_as_read(message_id)
        
        # Procesar según el tipo de mensaje
        if message_type == 'text' and message_text:
            logger.info(f"📩 Mensaje WhatsApp de {user_id}: {message_text[:50]}")
            
            # Procesar mensaje (lógica común)
            response = await process_message(
                platform="whatsapp",
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
        logger.error(f"Error procesando webhook WhatsApp: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.get("/health")
async def whatsapp_health():
    """
    Health check del servicio de WhatsApp.
    """
    all_sessions = get_all_sessions()
    whatsapp_sessions = {
        k: v for k, v in all_sessions.items() 
        if v.get('platform') == 'whatsapp'
    }
    
    return {
        "status": "ok",
        "whatsapp_configured": bool(WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID),
        "webhook_token_configured": bool(WEBHOOK_VERIFY_TOKEN),
        "active_sessions": len(whatsapp_sessions),
        "timestamp": get_timestamp()
    }
