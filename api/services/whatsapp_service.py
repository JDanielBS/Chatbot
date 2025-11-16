"""
Servicio de procesamiento de mensajes de WhatsApp.
"""
import os
import logging

from api.dependencies import (
    get_rag_manager,
    get_llm_gemini,
    increment_query_counter
)
from api.utils.whatsapp_helpers import (
    get_session,
    hash_phone_number
)
from api.utils.whatsapp_logger import log_interaction
from api.config.whatsapp_messages import (
    get_welcome_message,
    get_policy_message,
    get_command_message,
    format_sources_message
)

logger = logging.getLogger(__name__)


def get_sources_message() -> str:
    try:
        rag = get_rag_manager()
        stats = rag.get_stats()
        total_chunks = stats.get('total_chunks', 0)
        
        try:
            sample_docs = rag.retrieve_documents("inteligencia artificial", k=20, include_scores=False)
            
            unique_sources = set()
            for doc in sample_docs:
                source = doc.metadata.get("original_filename") or doc.metadata.get("source", "Desconocido")
                if source and source != "Desconocido":
                    if os.path.sep in source:
                        source = os.path.basename(source)
                    unique_sources.add(source)
            
            sources_list = [f"• {source}" for source in sorted(unique_sources)]
            
            if sources_list:
                return format_sources_message(sources_list, total_chunks, error=False)
            else:
                logger.warning("No se encontraron fuentes en la base de datos")
                return format_sources_message([], total_chunks, error=True)
            
        except Exception as e:
            logger.error(f"Error obteniendo fuentes de la BD: {e}")
            return format_sources_message([], total_chunks, error=True)
            
    except Exception as e:
        logger.error(f"Error obteniendo fuentes: {e}")
        return format_sources_message([], 0, error=True)


async def process_whatsapp_message(message_text: str, phone_number: str) -> str:
    session = get_session(phone_number)
    message_upper = message_text.strip().upper()
    
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
    
    if message_upper == "ACEPTO":
        session['opt_in'] = True
        return get_command_message("opt_in_success")
    
    if message_upper == "SALIR":
        session['opt_in'] = False
        return get_command_message("opt_out_success")
    
    if not session['opt_in']:
        return get_welcome_message()
    
    return await _process_ai_question(message_text, session, phone_number)


async def _process_ai_question(message_text: str, session: dict, phone_number: str) -> str:
    try:
        rag = get_rag_manager()
        llm = get_llm_gemini()
        thread_id = session['thread_id']
        mode = session.get('mode', 'extended')
        
        query_count = increment_query_counter()
        
        context = ""
        sources_with_scores = []
        
        try:
            retrieved_docs = rag.retrieve_documents(message_text, k=6, include_scores=True)
            
            if retrieved_docs:
                for i, (doc, score) in enumerate(retrieved_docs, 1):
                    source_name = doc.metadata.get("original_filename") or doc.metadata.get("source", "Desconocido")
                    sources_with_scores.append((source_name, score))
                
                context_parts = []
                for i, (doc, score) in enumerate(retrieved_docs, 1):
                    source = doc.metadata.get("original_filename") or doc.metadata.get("source", "Desconocido")
                    context_parts.append(f"[Fuente {i}: {source} | score={score:.4f}]\n{doc.page_content}")
                context = "\n\n".join(context_parts)
        except Exception as e:
            logger.error(f"Error en búsqueda RAG: {e}")
        
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
        
        response_ai = llm.process_question(enhanced_prompt)
        response_text = response_ai.content if hasattr(response_ai, 'content') else str(response_ai)
        
        log_interaction(
            session_hash=hash_phone_number(phone_number),
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

