"""
Servicio común de procesamiento de mensajes.
Funciona para cualquier plataforma (WhatsApp, Telegram, etc.)
"""
import os
import logging
from typing import Dict

from api.dependencies import (
    get_rag_manager,
    get_llm_gemini,
    increment_query_counter
)
from api.utils.session_manager import get_session, hash_user_id
from api.utils.message_logger import log_interaction
from api.config.messages import (
    get_welcome_message,
    get_policy_message,
    get_command_message,
    format_sources_message
)

logger = logging.getLogger(__name__)


def get_sources_message() -> str:
    """
    Retorna la lista de fuentes confiables desde la base de datos.
    
    Returns:
        str: Mensaje con lista de fuentes
    """
    try:
        rag = get_rag_manager()
        stats = rag.get_stats()
        total_chunks = stats.get('total_chunks', 0)
        
        try:
            # Hacer una búsqueda amplia para obtener muestras de documentos
            sample_docs = rag.retrieve_documents("inteligencia artificial", k=20, include_scores=False)
            
            # Extraer nombres únicos de archivos
            unique_sources = set()
            for doc in sample_docs:
                source = doc.metadata.get("original_filename") or doc.metadata.get("source", "Desconocido")
                if source and source != "Desconocido":
                    # Limpiar la ruta para mostrar solo el nombre del archivo
                    if os.path.sep in source:
                        source = os.path.basename(source)
                    unique_sources.add(source)
            
            # Construir lista formateada
            sources_list = [f"• {source}" for source in sorted(unique_sources)]
            
            # Formatear mensaje (sin else, solo si hay fuentes)
            if sources_list:
                return format_sources_message(sources_list, total_chunks, error=False)
            else:
                # Si no hay fuentes, es un error
                logger.warning("No se encontraron fuentes en la base de datos")
                return format_sources_message([], total_chunks, error=True)
            
        except Exception as e:
            logger.error(f"Error obteniendo fuentes de la BD: {e}")
            # Error al acceder a la BD
            return format_sources_message([], total_chunks, error=True)
            
    except Exception as e:
        logger.error(f"Error obteniendo fuentes: {e}")
        return format_sources_message([], 0, error=True)


async def process_message(
    platform: str,
    user_id: str,
    message_text: str,
    message_id: str = None
) -> str:
    """
    Procesa un mensaje de cualquier plataforma.
    
    Args:
        platform: Nombre de la plataforma (whatsapp, telegram, etc.)
        user_id: ID del usuario en esa plataforma
        message_text: Texto del mensaje
        message_id: ID del mensaje (opcional)
        
    Returns:
        str: Respuesta del bot
    """
    session = get_session(platform, user_id)
    message_upper = message_text.strip().upper()
    
    # Comandos especiales (funcionan sin opt-in)
    if message_upper in ["POLÍTICA", "POLITICA"]:
        return get_policy_message()
    
    if message_upper in ["FUENTE", "FUENTES", "FUENTE(S)"]:
        return get_sources_message()
    
    if message_upper == "MODO BREVE":
        session['mode'] = 'brief'
        return get_command_message("mode_brief_activated")
    
    if message_upper == "MODO EXTENDIDO":
        session['mode'] = 'extended'
        return get_command_message("mode_extended_activated")
    
    # Opt-in
    if message_upper == "ACEPTO":
        session['opt_in'] = True
        return get_command_message("opt_in_success")
    
    # Opt-out
    if message_upper == "SALIR":
        session['opt_in'] = False
        return get_command_message("opt_out_success")
    
    # Si no ha hecho opt-in, mostrar bienvenida
    if not session['opt_in']:
        return get_welcome_message()
    
    # Procesar pregunta con RAG y LLM
    return await _process_ai_question(message_text, session, platform, user_id)


async def _process_ai_question(
    message_text: str,
    session: dict,
    platform: str,
    user_id: str
) -> str:
    """
    Procesa una pregunta usando RAG y LLM.
    
    Args:
        message_text: Texto de la pregunta
        session: Sesión del usuario
        platform: Nombre de la plataforma
        user_id: ID del usuario
        
    Returns:
        str: Respuesta del bot
    """
    try:
        rag = get_rag_manager()
        llm = get_llm_gemini()
        thread_id = session['thread_id']
        mode = session.get('mode', 'extended')
        
        # Incrementar contador
        query_count = increment_query_counter()
        
        # Buscar documentos relevantes con RAG
        context = ""
        sources_with_scores = []
        
        try:
            retrieved_docs = rag.retrieve_documents(message_text, k=6, include_scores=True)
            
            if retrieved_docs:
                for i, (doc, score) in enumerate(retrieved_docs, 1):
                    source_name = doc.metadata.get("original_filename") or doc.metadata.get("source", "Desconocido")
                    sources_with_scores.append((source_name, score))
                
                # Construir contexto para el prompt
                context_parts = []
                for i, (doc, score) in enumerate(retrieved_docs, 1):
                    source = doc.metadata.get("original_filename") or doc.metadata.get("source", "Desconocido")
                    context_parts.append(f"[Fuente {i}: {source} | score={score:.4f}]\n{doc.page_content}")
                context = "\n\n".join(context_parts)
        except Exception as e:
            logger.error(f"Error en búsqueda RAG: {e}")
        
        # Construir prompt según el modo
        mode_instructions = {
            "brief": "Responde de forma breve y concisa (máximo 2-3 párrafos cortos).",
            "extended": "Proporciona una respuesta detallada y explicativa con citas."
        }
        mode_instruction = mode_instructions.get(mode, mode_instructions["extended"])
        
        if context:
            enhanced_prompt = f"""Eres un asistente experto en Inteligencia Artificial.

{mode_instruction}

Usa la siguiente información de documentos confiables para responder la pregunta. 
Si la información no está en los documentos, indícalo claramente.
SIEMPRE cita las fuentes cuando uses información de los documentos.

CONTEXTO DE DOCUMENTOS:
{context}

PREGUNTA DEL USUARIO:
{message_text}

INSTRUCCIONES:
- Responde de forma precisa basándote en el contexto
- Cita las fuentes mencionando el documento
- Si algo no está en los documentos, puedes usar tu conocimiento pero indícalo
- Sé claro, educativo y preciso
- Adapta tu respuesta al modo {mode}
"""
        else:
            enhanced_prompt = f"""Eres un asistente experto en Inteligencia Artificial.

{mode_instruction}

PREGUNTA DEL USUARIO:
{message_text}

Nota: No se encontró información específica en los documentos indexados, 
pero puedes responder basándote en tu conocimiento general sobre IA.
"""
        
        # Procesar con el LLM
        response_ai = llm.process_question(enhanced_prompt)
        response_text = response_ai.content if hasattr(response_ai, 'content') else str(response_ai)
        
        # Log anonimizado (sin PII)
        log_interaction(
            session_hash=hash_user_id(platform, user_id),
            platform=platform,
            message_length=len(message_text),
            response_length=len(response_text),
            mode=mode,
            query_number=query_count,
            sources_found=len(sources_with_scores)
        )
        
        return response_text
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        import traceback
        traceback.print_exc()
        return get_command_message("error_processing")


