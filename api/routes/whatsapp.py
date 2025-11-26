import os
import logging
import json
from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import PlainTextResponse

from api.services.message_service import process_message
from api.services.platform_handlers import get_platform_client
from api.config.messages import get_command_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """Verificación del webhook de WhatsApp/Meta."""
    verify_token = os.getenv("WEBHOOK_VERIFY_TOKEN", "mi_token_secreto_123")
    
    logger.info(f"═══════════════════════════════════════════════════")
    logger.info(f"🔐 [WHATSAPP VERIFY] Verificación webhook recibida")
    logger.info(f"   → hub.mode: {hub_mode}")
    logger.info(f"   → hub.verify_token recibido: {hub_verify_token}")
    logger.info(f"   → hub.verify_token esperado: {verify_token}")
    logger.info(f"   → hub.challenge: {hub_challenge}")
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info("✅ [WHATSAPP] Webhook verificado correctamente")
        return PlainTextResponse(content=hub_challenge)
    
    logger.warning(f"❌ [WHATSAPP] Verificación fallida")
    logger.warning(f"   → Token coincide: {hub_verify_token == verify_token}")
    logger.warning(f"   → Mode es subscribe: {hub_mode == 'subscribe'}")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_message(request: Request):
    try:
        data = await request.json()
        logger.info(f"═══════════════════════════════════════════════════")
        logger.info(f"📩 [WHATSAPP WEBHOOK] Datos recibidos:")
        logger.info(f"   → JSON completo: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        client = get_platform_client("whatsapp")
        
        message_data = client.extract_message_data(data)
        logger.info(f"   → Datos extraídos: {message_data}")
        
        if not message_data:
            logger.warning(f"⚠️ [WHATSAPP] No se pudo extraer datos del mensaje (puede ser status update)")
            return {"status": "ok"}
        
        user_id = message_data['user_id']
        message_id = message_data.get('message_id')
        message_type = message_data.get('message_type', 'text')
        message_text = message_data.get('message_text')
        
        logger.info(f"   → user_id: {user_id}")
        logger.info(f"   → message_id: {message_id}")
        logger.info(f"   → message_type: {message_type}")
        logger.info(f"   → message_text: {message_text[:100] if message_text else 'None'}...")
        
        if message_id:
            logger.info(f"📖 [WHATSAPP] Marcando mensaje como leído: {message_id}")
            client.mark_as_read(message_id)
        
        if message_type == 'text' and message_text:
            logger.info(f"📝 [WHATSAPP] Procesando mensaje de texto de {user_id}")
            
            response = await process_message(
                platform="whatsapp",
                user_id=user_id,
                message_text=message_text
            )
            
            logger.info(f"🤖 [WHATSAPP] Respuesta del LLM (primeros 200 chars): {response[:200] if response else 'VACÍA'}...")
            logger.info(f"   → Longitud respuesta: {len(response) if response else 0} caracteres")
            
            send_result = client.send_message(user_id, response)
            logger.info(f"   → Resultado envío: {'✅ Éxito' if send_result else '❌ Falló'}")
        
        elif message_type in ['image', 'audio', 'video', 'document']:
            logger.info(f"📎 [WHATSAPP] Recibido archivo tipo: {message_type}")
            response = get_command_message(f"{message_type}_received")
            if not response:
                response = get_command_message("image_received")  
            client.send_message(user_id, response)
        
        logger.info(f"═══════════════════════════════════════════════════")
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"❌ [WHATSAPP] Error procesando webhook: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"   → Traceback: {traceback.format_exc()}")
        return {"status": "error", "message": str(e)}
