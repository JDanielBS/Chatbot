"""
Endpoints relacionados con el chat y conversaciones.
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime

from api.models import ChatRequest, ChatResponse, Source
from api.dependencies import (
    get_rag_manager,
    get_llm_gemini,
    get_chain,
    increment_query_counter,
    format_sources_from_docs,
    get_timestamp
)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "/",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Enviar mensaje al chatbot",
    description="""
    Envía un mensaje al chatbot y recibe una respuesta con RAG.
    
    Características:
    - Usa RAG para buscar información en documentos indexados
    - Mantiene contexto de conversación con thread_id
    - Cita fuentes utilizadas
    - Registra métricas de rendimiento
    
    Modos:
    - brief: Respuestas cortas y concisas
    - extended: Respuestas detalladas con explicaciones
    """,
    responses={
        200: {"description": "Respuesta exitosa con fuentes citadas"},
        400: {"description": "Request inválido"},
        500: {"description": "Error interno del servidor"}
    }
)

async def chat(request: ChatRequest):
    """
    Procesa un mensaje del usuario y retorna respuesta del chatbot con RAG.
    
    Args:
        request: Objeto ChatRequest con el mensaje y configuración
        
    Returns:
        ChatResponse: Respuesta del chatbot con fuentes y métricas
        
    Raises:
        HTTPException: Si hay error procesando el mensaje
    """
    try:
        # Incrementar contador de consultas
        query_count = increment_query_counter()
        
        # Obtener componentes necesarios
        rag = get_rag_manager()
        llm = get_llm_gemini()
        chain = get_chain()
        
        sources_list = []
        context = ""
        sources_with_scores = []
        
        # Si usa RAG, buscar documentos relevantes
        if request.use_rag:
            try:
                # Usar retrieve_documents para obtener documentos completos con scores
                retrieved_docs = rag.retrieve_documents(request.message, k=6, include_scores=True)
                
                if retrieved_docs:
                    # Convertir documentos a formato de fuentes con excerpts
                    for i, (doc, score) in enumerate(retrieved_docs, 1):
                        source_name = doc.metadata.get("original_filename") or doc.metadata.get("source", "Desconocido")
                        page = doc.metadata.get("page", None)
                        
                        # Crear excerpt truncado del contenido (primeros 150 caracteres)
                        excerpt = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                        
                        sources_list.append({
                            "document": source_name,
                            "page": page,
                            "relevance_score": round(score, 4),
                            "excerpt": excerpt
                        })
                        sources_with_scores.append((source_name, score))
                    
                    # Construir contexto para el prompt
                    context_parts = []
                    for i, (doc, score) in enumerate(retrieved_docs, 1):
                        source = doc.metadata.get("original_filename") or doc.metadata.get("source", "Desconocido")
                        context_parts.append(f"[Fuente {i}: {source} | score={score:.4f}]\n{doc.page_content}")
                    context = "\n\n".join(context_parts)
                    
                    print(f"{len(sources_list)} fuentes encontradas con scores")
                else:
                    print("No se encontraron documentos relevantes")
                    
            except Exception as e:
                print(f"Error en búsqueda RAG: {e}")
                import traceback
                traceback.print_exc()
        
        mode_instructions = {
            "brief": "Responde de forma breve y concisa (máximo 2-3 párrafos cortos).",
            "extended": "Proporciona una respuesta detallada y explicativa."
        }
        
        mode_instruction = mode_instructions.get(request.mode, mode_instructions["extended"])
        
        if context:
            enhanced_prompt = f"""Eres un asistente experto en Inteligencia Artificial.

{mode_instruction}

Usa la siguiente información de documentos confiables para responder la pregunta. 
Si la información no está en los documentos, indícalo claramente.
SIEMPRE cita las fuentes cuando uses información de los documentos.

CONTEXTO DE DOCUMENTOS:
{context}

PREGUNTA DEL USUARIO:
{request.message}

INSTRUCCIONES:
- Responde de forma precisa basándote en el contexto
- Cita las fuentes mencionando el documento
- Si algo no está en los documentos, puedes usar tu conocimiento pero indícalo
- Sé claro, educativo y preciso
"""
        else:
            enhanced_prompt = f"""Eres un asistente experto en Inteligencia Artificial.

{mode_instruction}

PREGUNTA DEL USUARIO:
{request.message}

Nota: No se encontró información específica en los documentos indexados, 
pero puedes responder basándote en tu conocimiento general sobre IA.
"""
        
        # Procesar con el LLM
        # Nota: Aquí usamos process_question directamente porque chain.invoke tiene un bug
        # En una futura actualización, deberíamos usar el chain completo
        response_text = llm.process_question(enhanced_prompt)
        
        # Construir respuesta con métricas mejoradas
        chat_response = ChatResponse(
            response=response_text,
            sources=[Source(**s) for s in sources_list],
            thread_id=request.thread_id,
            model_used=request.model_name,
            timestamp=get_timestamp(),
            metrics={
                "query_number": query_count,
                "context_used": len(context) > 0,
                "sources_found": len(sources_list),
                "mode": request.mode,
                "avg_relevance_score": round(sum(score for _, score in sources_with_scores) / len(sources_with_scores), 4) if sources_with_scores else 0.0
            }
        )
        
        return chat_response
        
    except Exception as e:
        print(f"Error en endpoint /chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando el mensaje: {str(e)}"
        )


@router.get(
    "/history/{thread_id}",
    summary="Obtener historial de conversación",
    description="Obtiene el historial de mensajes de una conversación específica",
    tags=["Chat"]
)
async def get_history(thread_id: str):
    """
    Obtiene el historial de una conversación.
    
    TODO: Implementar en Fase 2 cuando se agregue persistencia de conversaciones.
    """
    return {
        "message": "Endpoint en desarrollo",
        "thread_id": thread_id,
        "history": []
    }


@router.delete(
    "/history/{thread_id}",
    summary="Eliminar historial de conversación",
    description="Elimina el historial de una conversación específica",
    tags=["Chat"]
)
async def delete_history(thread_id: str):
    """
    Elimina el historial de una conversación.
    
    TODO: Implementar luego
    """
    return {
        "message": "Endpoint en desarrollo",
        "thread_id": thread_id,
        "deleted": False
    }

