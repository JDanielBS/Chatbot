"""
Endpoints relacionados con el sistema, métricas y health checks.
"""

from fastapi import APIRouter, status

from api.models import HealthResponse, SystemStats
from api.dependencies import (
    get_rag_manager,
    get_query_counter,
    get_uptime,
    get_available_models,
    check_component_health,
    get_timestamp,
    get_settings
)

router = APIRouter(tags=["System"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check del sistema",
    description="""
    Verifica el estado de salud de todos los componentes del sistema.
    
    **Componentes verificados:**
    - LLM (Gemini)
    - RAG Manager
    - Base de datos vectorial
    - Chain con LangGraph
    - Sistema de monitoreo
    
    **Estados posibles:**
    - `operational`: Componente funcionando correctamente
    - `degraded`: Componente funcionando con problemas
    - `error`: Componente con fallos
    """
)
async def health_check():
    """
    Verifica el estado de salud de todos los componentes.
    
    Returns:
        HealthResponse: Estado de salud del sistema
    """
    settings = get_settings()
    
    # Verificar componentes
    components = check_component_health()
    
    # Determinar estado general
    has_errors = any("error" in status for status in components.values())
    has_degraded = any("degraded" in status for status in components.values())
    
    if has_errors:
        overall_status = "unhealthy"
    elif has_degraded:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=get_timestamp(),
        version=settings["version"],
        components=components
    )


@router.get(
    "/stats",
    response_model=SystemStats,
    status_code=status.HTTP_200_OK,
    summary="Estadísticas del sistema",
    description="""
    Obtiene estadísticas detalladas del sistema y uso.
    
    **Información incluida:**
    - Estado general
    - Estadísticas del RAG (documentos, chunks, tamaño)
    - Total de consultas procesadas
    - Tiempo de actividad
    - Modelos LLM disponibles
    """
)
async def get_stats():
    """
    Obtiene estadísticas del sistema.
    
    Returns:
        SystemStats: Estadísticas del sistema
    """
    # Obtener estadísticas del RAG
    try:
        rag = get_rag_manager()
        rag_stats = rag.get_stats()
        
        # Agregar información adicional
        if rag.is_empty():
            rag_stats["warning"] = "Base de datos vectorial vacía"
        
        # Convertir tamaño de la base de datos si es posible
        import os
        if os.path.exists(rag.persist_directory):
            total_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, _, filenames in os.walk(rag.persist_directory)
                for filename in filenames
            )
            rag_stats["database_size_mb"] = round(total_size / (1024 * 1024), 2)
        
    except Exception as e:
        rag_stats = {
            "error": str(e),
            "status": "Error"
        }
    
    # Obtener contador de consultas
    total_queries = get_query_counter()
    
    # Obtener tiempo de actividad
    uptime = get_uptime()
    
    # Obtener modelos disponibles
    models = get_available_models()
    
    # Determinar estado general
    components = check_component_health()
    has_errors = any("error" in status for status in components.values())
    
    overall_status = "unhealthy" if has_errors else "healthy"
    
    return SystemStats(
        status=overall_status,
        rag_stats=rag_stats,
        total_queries=total_queries,
        uptime_seconds=round(uptime, 2),
        models_available=models
    )


@router.get(
    "/info",
    summary="Información de la API",
    description="Obtiene información general sobre la API",
    tags=["System"]
)
async def get_info():
    """
    Obtiene información general de la API.
    
    Returns:
        dict: Información de la aplicación
    """
    settings = get_settings()
    
    return {
        "app_name": settings["app_name"],
        "version": settings["version"],
        "description": settings["description"],
        "documentation": {
            "swagger": settings["docs_url"],
            "redoc": settings["redoc_url"]
        },
        "endpoints": {
            "chat": "/api/chat",
            "health": "/api/health",
            "stats": "/api/stats",
            "documents": "/api/documents",
            "sources": "/api/sources",
            "feedback": "/api/feedback",
            "compare": "/api/chat/compare"
        },
        "features": {
            "rag": "Retrieval-Augmented Generation",
            "memory": "Conversational memory with LangGraph",
            "monitoring": "Performance metrics and logging",
            "multi_model": "Multiple LLM support"
        }
    }


@router.get(
    "/metrics",
    summary="Métricas detalladas",
    description="Obtiene métricas detalladas de rendimiento",
    tags=["System"]
)
async def get_metrics():
    """
    Obtiene métricas detalladas del sistema.
    
    TODO: Implementar luego con lectura del CSV de métricas.
    
    Incluirá:
    - Latencia promedio
    - Uso de tokens
    - Costos estimados
    - Distribución de modelos usados
    - etc.
    """
    return {
        "message": "Endpoint en desarrollo",
        "note": "Las métricas se están registrando en metrics/ia_metrics_report.csv",
    }

