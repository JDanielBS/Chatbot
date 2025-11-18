import logging
from fastapi import APIRouter, Request

from api.services.message_service import process_message
from api.services.platform_handlers import get_platform_client
from api.config.messages import get_command_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

@router.post("/webhook")
async def receive_message(request: Request):
    try:
        data = await request.json()
        logger.info(f"Webhook WhatsApp recibido: {data.get('entry', [])}")
        
        client = get_platform_client("whatsapp")
        
        message_data = client.extract_message_data(data)
        
        if not message_data:
            return {"status": "ok"}
        
        user_id = message_data['user_id']
        message_id = message_data.get('message_id')
        message_type = message_data.get('message_type', 'text')
        message_text = message_data.get('message_text')
        
        if message_id:
            client.mark_as_read(message_id)
        
        if message_type == 'text' and message_text:
            logger.info(f"Mensaje WhatsApp de {user_id}: {message_text[:50]}")
            
            response = await process_message(
                platform="whatsapp",
                user_id=user_id,
                message_text=message_text
            )
            
            client.send_message(user_id, response)
        
        elif message_type in ['image', 'audio', 'video', 'document']:
            response = get_command_message(f"{message_type}_received")
            if not response:
                response = get_command_message("image_received")  
            client.send_message(user_id, response)
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Error procesando webhook WhatsApp: {str(e)}")
        return {"status": "error", "message": str(e)}
