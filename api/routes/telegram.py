import logging
import json
from fastapi import APIRouter, Request

from api.services.message_service import process_message
from api.services.platform_handlers import get_platform_client
from api.config.messages import get_command_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["Telegram"])

@router.post("/webhook")
async def receive_message(request: Request):
    try:
        data = await request.json()
        logger.info(f"═══════════════════════════════════════════════════")
        logger.info(f"📩 [TELEGRAM WEBHOOK] Datos recibidos:")
        logger.info(f"   → update_id: {data.get('update_id')}")
        logger.info(f"   → JSON completo: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        client = get_platform_client("telegram")
        
        message_data = client.extract_message_data(data)
        logger.info(f"   → Datos extraídos: {message_data}")
        
        if not message_data:
            logger.warning(f"⚠️ [TELEGRAM] No se pudo extraer datos del mensaje")
            return {"status": "ok"}
        
        user_id = message_data['user_id']
        message_type = message_data.get('message_type', 'text')
        message_text = message_data.get('message_text')
        
        logger.info(f"   → user_id: {user_id}")
        logger.info(f"   → message_type: {message_type}")
        logger.info(f"   → message_text: {message_text[:100] if message_text else 'None'}...")
        
        if message_type == 'text' and message_text:
            logger.info(f"📝 [TELEGRAM] Procesando mensaje de texto de {user_id}")
            
            response = await process_message(
                platform="telegram",
                user_id=user_id,
                message_text=message_text
            )
            
            logger.info(f"🤖 [TELEGRAM] Respuesta del LLM (primeros 200 chars): {response[:200] if response else 'VACÍA'}...")
            logger.info(f"   → Longitud respuesta: {len(response) if response else 0} caracteres")
            
            send_result = client.send_message(user_id, response)
            logger.info(f"   → Resultado envío: {'✅ Éxito' if send_result else '❌ Falló'}")
        
        elif message_type in ['image', 'audio', 'video', 'document']:
            logger.info(f"📎 [TELEGRAM] Recibido archivo tipo: {message_type}")
            response = get_command_message(f"{message_type}_received")
            if not response:
                response = get_command_message("image_received")  
            client.send_message(user_id, response)
        
        logger.info(f"═══════════════════════════════════════════════════")
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"❌ [TELEGRAM] Error procesando webhook: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"   → Traceback: {traceback.format_exc()}")
        return {"status": "error", "message": str(e)}

