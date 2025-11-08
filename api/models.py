"""
Este módulo define todos los schemas utilizados en los endpoints de la API,
incluyendo modelos para chat, documentos, métricas y respuestas del sistema.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# MODELOS DE CHAT
# ============================================================================

class ChatRequest(BaseModel):
    """
    Modelo para las solicitudes de chat.
    
    Attributes:
        message: Mensaje del usuario
        thread_id: ID de la sesión/conversación (para mantener contexto)
        use_rag: Si debe usar RAG o solo el LLM directo
        model_name: Nombre del modelo a usar (gemini, gpt4, llama, etc.)
        mode: Modo de respuesta (brief/extended)
    """
    message: str = Field(..., description="Mensaje/pregunta del usuario", min_length=1)
    thread_id: Optional[str] = Field(default="default", description="ID de la conversación")
    use_rag: bool = Field(default=True, description="Usar RAG para responder")
    model_name: str = Field(default="gemini", description="Modelo LLM a usar")
    mode: str = Field(default="extended", description="Modo: 'brief' o 'extended'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "¿Qué es la inteligencia artificial?",
                "thread_id": "user_123",
                "use_rag": True,
                "model_name": "gemini",
                "mode": "extended"
            }
        }


class Source(BaseModel):
    """
    Información sobre una fuente citada en la respuesta.
    
    Attributes:
        document: Nombre del documento fuente
        page: Número de página (si aplica)
        relevance_score: Score de relevancia (0-1)
        excerpt: Extracto del texto relevante
    """
    document: str = Field(..., description="Nombre del documento")
    page: Optional[int] = Field(default=None, description="Número de página")
    relevance_score: Optional[float] = Field(default=None, description="Score de similitud")
    excerpt: str = Field(..., description="Fragmento relevante del documento")


class ChatResponse(BaseModel):
    """
    Respuesta del chatbot con metadata.
    
    Attributes:
        response: Texto de la respuesta del bot
        sources: Lista de fuentes utilizadas
        thread_id: ID de la conversación
        model_used: Modelo que generó la respuesta
        timestamp: Momento de la respuesta, cuándo respondió
        metrics: Métricas de rendimiento (latencia, tokens, etc.)
    """
    response: str = Field(..., description="Respuesta del chatbot")
    sources: List[Source] = Field(default=[], description="Fuentes citadas")
    thread_id: str = Field(..., description="ID de la conversación")
    model_used: str = Field(..., description="Modelo LLM utilizado")
    timestamp: str = Field(..., description="Timestamp de la respuesta")
    metrics: Dict[str, Any] = Field(default={}, description="Métricas de rendimiento")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "La inteligencia artificial es...",
                "sources": [
                    {
                        "document": "unesco_ai_ethics.pdf",
                        "page": 5,
                        "relevance_score": 0.92,
                        "excerpt": "La IA se define como..."
                    }
                ],
                "thread_id": "user_123",
                "model_used": "gemini-2.0-flash-lite",
                "timestamp": "2024-01-15T10:30:00",
                "metrics": {
                    "latency_ms": 1250.5,
                    "input_tokens": 150,
                    "output_tokens": 300,
                    "cost_usd": 0.0002
                }
            }
        }


# ============================================================================
# MODELOS DE COMPARACIÓN 
# ============================================================================

class CompareRequest(BaseModel):
    """
    Solicitud para comparar respuestas de múltiples modelos.
    """
    message: str = Field(..., description="Pregunta a comparar")
    models: List[str] = Field(..., description="Lista de modelos a comparar", min_items=2)
    thread_id: Optional[str] = Field(default="default")
    use_rag: bool = Field(default=True)


class ModelComparison(BaseModel):
    """
    Comparación de un modelo específico.
    """
    model_name: str
    response: str
    sources: List[Source]
    metrics: Dict[str, Any]


class CompareResponse(BaseModel):
    """
    Respuesta con comparación de múltiples modelos.
    """
    message: str
    comparisons: List[ModelComparison]
    timestamp: str


# ============================================================================
# MODELOS DE DOCUMENTOS 
# ============================================================================

class DocumentInfo(BaseModel):
    """
    Información sobre un documento en la base de conocimiento.
    """
    filename: str = Field(..., description="Nombre del archivo")
    title: Optional[str] = Field(default=None, description="Título del documento")
    author: Optional[str] = Field(default=None, description="Autor")
    year: Optional[int] = Field(default=None, description="Año de publicación")
    pages: Optional[int] = Field(default=None, description="Número de páginas")
    chunks: int = Field(..., description="Número de chunks indexados")
    date_added: str = Field(..., description="Fecha de indexación")


class DocumentListResponse(BaseModel):
    """
    Lista de documentos disponibles.
    """
    total_documents: int
    documents: List[DocumentInfo]


class UploadResponse(BaseModel):
    """
    Respuesta al subir un documento.
    """
    success: bool
    message: str
    filename: str
    chunks_created: int


# ============================================================================
# MODELOS DE MÉTRICAS Y STATS
# ============================================================================

class SystemStats(BaseModel):
    """
    Estadísticas del sistema.
    
    Attributes:
        status: Estado del sistema
        rag_stats: Estadísticas de la base vectorial
        total_queries: Total de consultas procesadas
        uptime: Tiempo de actividad
        models_available: Modelos LLM disponibles
    """
    status: str = Field(..., description="Estado general del sistema")
    rag_stats: Dict[str, Any] = Field(..., description="Estadísticas del RAG")
    total_queries: int = Field(..., description="Total de consultas procesadas")
    uptime_seconds: float = Field(..., description="Tiempo activo en segundos")
    models_available: List[str] = Field(..., description="Modelos LLM disponibles")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "rag_stats": {
                    "total_chunks": 450,
                    "total_documents": 9,
                    "chunk_size": 1000,
                    "database_size_mb": 12.5
                },
                "total_queries": 156,
                "uptime_seconds": 3600.5,
                "models_available": ["gemini", "gpt4", "llama"]
            }
        }


class HealthResponse(BaseModel):
    """
    Respuesta del health check.
    """
    status: str = Field(..., description="Estado: 'healthy' o 'unhealthy'")
    timestamp: str = Field(..., description="Timestamp del check")
    version: str = Field(default="1.0.0", description="Versión de la API")
    components: Dict[str, str] = Field(..., description="Estado de componentes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00",
                "version": "1.0.0",
                "components": {
                    "llm": "operational",
                    "rag": "operational",
                    "vector_db": "operational",
                    "monitoring": "operational"
                }
            }
        }


# ============================================================================
# MODELOS DE FEEDBACK 
# ============================================================================

class FeedbackRequest(BaseModel):
    """
    Feedback del usuario sobre una respuesta.
    """
    thread_id: str = Field(..., description="ID de la conversación")
    message_id: Optional[str] = Field(default=None, description="ID del mensaje evaluado")
    rating: int = Field(..., description="Rating 1-5", ge=1, le=5)
    feedback_type: str = Field(..., description="Tipo: 'helpful', 'not_helpful', 'incorrect'")
    comment: Optional[str] = Field(default=None, description="Comentario adicional")


class FeedbackResponse(BaseModel):
    """
    Confirmación de feedback recibido.
    """
    success: bool
    message: str
    feedback_id: str


# ============================================================================
# MODELOS DE ERROR
# ============================================================================

class ErrorResponse(BaseModel):
    """
    Respuesta de error estándar.
    """
    error: str = Field(..., description="Tipo de error")
    message: str = Field(..., description="Descripción del error")
    timestamp: str = Field(..., description="Momento del error")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Detalles adicionales")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "El campo 'message' no puede estar vacío",
                "timestamp": "2024-01-15T10:30:00",
                "details": {"field": "message", "constraint": "min_length"}
            }
        }

