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
    
    **Características:**
    - Usa RAG para buscar información en documentos indexados
    - Mantiene contexto de conversación con thread_id
    - Cita fuentes utilizadas
    - Registra métricas de rendimiento
    
    **Modos:**
    - `brief`: Respuestas cortas y concisas
    - `extended`: Respuestas detalladas con explicaciones
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
        
        # Llamar al chain: dejar que el chain decida si hace RAG según request.use_rag
        # Pedimos metadata para construir la lista de fuentes en la respuesta
        response_text, metadata = chain.invoke(
            request.message,
            request.thread_id,
            use_rag=request.use_rag,
            return_metadata=True
        )

        # Reconstruir lista de fuentes desde metadata (si existe)
        sources_list = []
        for item in metadata.get("sources_with_scores", []) if metadata else []:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                doc_name, score = item[0], item[1]
                sources_list.append({
                    "document": doc_name,
                    "page": None,
                    "relevance_score": score,
                    "excerpt": ""
                })
            elif isinstance(item, dict):
                sources_list.append({
                    "document": item.get("document") or item.get("source"),
                    "page": item.get("page"),
                    "relevance_score": item.get("relevance_score") or item.get("score"),
                    "excerpt": item.get("excerpt", "")
                })
            else:
                sources_list.append({"document": str(item), "page": None, "relevance_score": None, "excerpt": ""})
        
        # Construir respuesta
        chat_response = ChatResponse(
            response=response_text,
            sources=[Source(**s) for s in sources_list],
            thread_id=request.thread_id,
            model_used=request.model_name,
            timestamp=get_timestamp(),
            metrics={
                "query_number": query_count,
                "context_used": (metadata.get("context_size", 0) > 0) if metadata else False,
                "sources_found": len(sources_list),
                "mode": request.mode
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

