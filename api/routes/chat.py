"""
Endpoints relacionados con el chat y conversaciones.
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime

from api.models import ChatRequest, ChatResponse, Source
from api.dependencies import (
    get_chain,
    increment_query_counter,
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
        
        # Obtener chain
        chain = get_chain()
        
        # Invocar el chain completo (maneja RAG, LLM y métricas internamente)
        response_text, metadata = chain.invoke(
            inputs=request.message,
            thread_id=request.thread_id,
            use_rag=request.use_rag,
            return_metadata=True
        )
        
        # Extraer fuentes desde metadata (si existen)
        sources_list = []
        sources_with_scores = metadata.get("sources_with_scores", [])
        
        if sources_with_scores:
            # Convertir a formato API
            for source, score in sources_with_scores:
                sources_list.append({
                    "document": source,
                    "page": None,
                    "relevance_score": round(score, 4),
                    "excerpt": ""  # El chain no incluye excerpts en metadata
                })
        
        # Construir respuesta
        chat_response = ChatResponse(
            response=response_text,
            sources=[Source(**s) for s in sources_list],
            thread_id=request.thread_id,
            model_used=request.model_name,
            timestamp=get_timestamp(),
            metrics={
                "query_number": query_count,
                "context_used": metadata.get("context_size", 0) > 0,
                "sources_found": len(sources_list),
                "mode": request.mode,
                "avg_relevance_score": round(
                    sum(score for _, score in sources_with_scores) / len(sources_with_scores), 4
                ) if sources_with_scores else 0.0
            }
        )
        
        return chat_response
        
    except Exception as e:
        print(f"Error en endpoint /chat: {e}")
        import traceback
        traceback.print_exc()
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

