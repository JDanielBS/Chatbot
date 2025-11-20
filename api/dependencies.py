"""
Dependencias compartidas para la API.

Este módulo maneja la inicialización de componentes singleton como:
- RAG Manager (base vectorial)
- LLM Instances
- Sistema de métricas
- Contadores globales
"""

import os
import time
from typing import Optional
from datetime import datetime
from functools import lru_cache

from src.llm.RAG_manager import RAGManager
from src.llm.Llm import IAExpertLLM
from src.chain.Chain import IAChain


# ============================================================================
# VARIABLES GLOBALES
# ============================================================================

_rag_manager: Optional[RAGManager] = None
_llm_gemini: Optional[IAExpertLLM] = None
_chain: Optional[IAChain] = None
_start_time = time.time()
_query_counter = 0

def get_rag_manager() -> RAGManager:
    """
    Obtiene o crea la instancia singleton del RAGManager.
    
    Returns:
        RAGManager: Instancia del gestor de RAG
        
    Raises:
        RuntimeError: Si hay error al inicializar el RAG
    """
    global _rag_manager
    
    if _rag_manager is None:
        try:
            print("Inicializando RAG Manager...")
            _rag_manager = RAGManager(
                persist_directory="./data/chroma_db",
                chunk_size=1000,
                chunk_overlap=200
            )
            
            if _rag_manager.is_empty():
                print("Advertencia: Base de datos vectorial está vacía")
                print("Ejecuta el script de indexación de documentos")
            else:
                stats = _rag_manager.get_stats()
                print(f"RAG Manager listo con {stats.get('total_chunks', 0)} chunks")
                
        except Exception as e:
            print(f"Error al inicializar RAG Manager: {e}")
            raise RuntimeError(f"No se pudo inicializar el RAG Manager: {e}")
    
    return _rag_manager


def get_llm_gemini() -> IAExpertLLM:
    """
    Obtiene o crea la instancia singleton del LLM Gemini.
    
    Returns:
        IAExpertLLM: Instancia del LLM de Gemini
        
    Raises:
        RuntimeError: Si hay error al inicializar el LLM
    """
    global _llm_gemini
    
    if _llm_gemini is None:
        try:
            print("Inicializando Gemini LLM...")
            _llm_gemini = IAExpertLLM()
            print("Gemini LLM listo")
        except Exception as e:
            print(f"Error al inicializar Gemini: {e}")
            raise RuntimeError(f"No se pudo inicializar Gemini LLM: {e}")
    
    return _llm_gemini


def get_chain() -> IAChain:
    """
    Obtiene o crea la instancia singleton del Chain con LangGraph.
    
    Returns:
        IAChain: Instancia del grafo conversacional
        
    Raises:
        RuntimeError: Si hay error al inicializar el Chain
    """
    global _chain
    
    if _chain is None:
        try:
            print("Inicializando Chain con LangGraph...")
            llm = get_llm_gemini()
            rag = get_rag_manager()
            _chain = IAChain(llm, rag)
            print("Chain listo con memoria persistente y RAG")
        except Exception as e:
            print(f"Error al inicializar Chain: {e}")
            raise RuntimeError(f"No se pudo inicializar Chain: {e}")
    
    return _chain


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def increment_query_counter() -> int:
    """
    Incrementa el contador global de consultas.
    
    Returns:
        int: Nuevo valor del contador
    """
    global _query_counter
    _query_counter += 1
    return _query_counter


def get_query_counter() -> int:
    """
    Obtiene el contador actual de consultas.
    
    Returns:
        int: Número de consultas procesadas
    """
    return _query_counter


def get_uptime() -> float:
    """
    Obtiene el tiempo de actividad del servidor en segundos.
    
    Returns:
        float: Segundos desde que se inició el servidor
    """
    return time.time() - _start_time


def get_available_models() -> list[str]:
    """
    Obtiene la lista de modelos LLM disponibles.
    
    Returns:
        list[str]: Lista de nombres de modelos disponibles
    """
    models = ["gemini"]
    
    if os.getenv("OPENAI_API_KEY"):
        models.append("gpt4")
        models.append("gpt3.5")
    
    if os.getenv("ANTHROPIC_API_KEY"):
        models.append("claude")

    return models


def check_component_health() -> dict:
    """
    Verifica el estado de salud de todos los componentes.
    
    Returns:
        dict: Estado de cada componente
    """
    components = {}
    
    try:
        llm = get_llm_gemini()
        components["llm"] = "operational"
    except Exception as e:
        components["llm"] = f"error: {str(e)[:50]}"
    
    try:
        rag = get_rag_manager()
        if rag.is_empty():
            components["rag"] = "operational_empty"
        else:
            components["rag"] = "operational"
    except Exception as e:
        components["rag"] = f"error: {str(e)[:50]}"
    
    try:
        rag = get_rag_manager()
        stats = rag.get_stats()
        if stats.get("status") == "operacional":
            components["vector_db"] = "operational"
        else:
            components["vector_db"] = "degraded"
    except Exception as e:
        components["vector_db"] = f"error: {str(e)[:50]}"
    
    try:
        chain = get_chain()
        components["chain"] = "operational"
    except Exception as e:
        components["chain"] = f"error: {str(e)[:50]}"
    
    try:
        from src.metrics.Monitoring import logger
        components["monitoring"] = "operational"
    except Exception as e:
        components["monitoring"] = f"error: {str(e)[:50]}"
    
    return components


def get_timestamp() -> str:
    """
    Obtiene timestamp en formato ISO.
    
    Returns:
        str: Timestamp actual en formato ISO
    """
    return datetime.now().isoformat()


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

@lru_cache()
def get_settings():
    """
    Obtiene configuración de la aplicación (cacheable).
    
    Returns:
        dict: Configuración de la aplicación
    """
    return {
        "app_name": "Chatbot IA - RAG API",
        "version": "1.0.0",
        "description": "API para chatbot especializado en Inteligencia Artificial con RAG",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "api_prefix": "/api",
        "cors_origins": ["*"],  
        "max_tokens_per_request": 4000,
        "default_retrieval_k": 4,
        "default_model": "gemini"
    }

