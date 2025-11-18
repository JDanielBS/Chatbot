import os
import logging

from api.dependencies import (
    get_chain,
    get_rag_manager,  
    increment_query_counter
)
from api.utils.session_manager import get_session, hash_user_id
from api.utils.message_logger import log_interaction
from api.utils.sources_metadata import get_all_sources_display
from api.config.messages import (
    get_welcome_message,
    get_policy_message,
    get_command_message,
    format_sources_message
)

logger = logging.getLogger(__name__)


async def get_sources_message(session: dict = None) -> str:
    """
    Retorna la lista de todas las fuentes confiables ordenadas alfabéticamente
    """
    try:
        # Obtener todas las fuentes del JSON
        sources_list = get_all_sources_display()
        
        if not sources_list:
            logger.warning("No se encontraron fuentes en el JSON de metadata")
            return format_sources_message([], error=True)
        
        formatted_sources = [f"• {source}" for source in sources_list]
        
        return format_sources_message(formatted_sources, error=False)
            
    except Exception as e:
        logger.error(f"Error obteniendo fuentes: {e}")
        return format_sources_message([], error=True)


async def process_message(
    platform: str,
    user_id: str,
    message_text: str,
) -> str:
    session = get_session(platform, user_id)
    message_upper = message_text.strip().upper()
    
    if message_upper in ["POLÍTICA", "POLITICA"]:
        return get_policy_message()
    
    if message_upper in ["FUENTE", "FUENTES", "FUENTE(S)"]:
        return await get_sources_message(session)
    
    if message_upper == "MODO BREVE":
        session['mode'] = 'brief'
        return get_command_message("mode_brief_activated")
    
    if message_upper == "MODO EXTENDIDO":
        session['mode'] = 'extended'
        return get_command_message("mode_extended_activated")
    
    if message_upper == "ACEPTO":
        session['opt_in'] = True
        return get_command_message("opt_in_success")
    
    if message_upper == "SALIR":
        session['opt_in'] = False
        return get_command_message("opt_out_success")
    
    if not session['opt_in']:
        return get_welcome_message()
    
    return await _process_ai_question(message_text, session, platform, user_id)


async def _process_ai_question(
    message_text: str,
    session: dict,
    platform: str,
    user_id: str
) -> str:
    try:
        chain = get_chain()
        thread_id = session['thread_id']
        mode = session.get('mode', 'extended')
        
        query_count = increment_query_counter()
        
        response_text, metadata = chain.invoke(
            inputs=message_text,
            thread_id=thread_id,
            use_rag=True,  
            return_metadata=True
        )
        
        session['last_metadata'] = metadata
        
        sources_with_scores = metadata.get("sources_with_scores", [])
        sources_count = len(sources_with_scores)
        
        log_interaction(
            session_hash=hash_user_id(platform, user_id),
            platform=platform,
            message_length=len(message_text),
            response_length=len(response_text),
            mode=mode,
            query_number=query_count,
            sources_found=sources_count
        )
        
        return response_text
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        import traceback
        traceback.print_exc()
        return get_command_message("error_processing")


