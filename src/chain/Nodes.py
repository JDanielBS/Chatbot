"""
Nodos del grafo de la cadena de IA.

Este módulo contiene los nodos simplificados que conforman el flujo de procesamiento.
"""
from langchain_core.messages import HumanMessage, AIMessage
from icecream import ic
import time

from src.chain.MetricsState import MetricsState
from src.metrics.Monitoring import MetricsCollector, logger
from src.prompts.Prompts import get_system_message


def rag_node(state: MetricsState, rag_manager) -> dict:
    """
    Nodo RAG: recupera contexto relevante de la base de conocimiento.
    
    Args:
        state: Estado actual del grafo
        rag_manager: Instancia de RAGManager
        
    Returns:
        dict: Estado actualizado con contexto y fuentes
    """
    # Extraer pregunta del mensaje
    question = state["messages"][-1].content if state["messages"] else None
    
    if not question:
        return {}
    
    # Recuperar contexto y fuentes
    context, sources_with_scores = rag_manager.build_context(question, k=8, use_retriever=True)
    
    # Calcular métricas de recuperación
    retrieval_metrics = MetricsCollector.calculate_retrieval_metrics(
        sources_with_scores, context
    )
    
    return {
        "context": context,
        "sources_with_scores": sources_with_scores,
        **retrieval_metrics
    }


def llm_node(state: MetricsState, llm_instance, rag_prompt, ia_prompt) -> dict:
    """
    Nodo LLM: genera respuesta usando el contexto si está disponible.
    
    Args:
        state: Estado actual del grafo
        llm_instance: Instancia del LLM
        rag_prompt: Prompt para usar con RAG
        ia_prompt: Prompt para usar sin RAG
        
    Returns:
        dict: Estado actualizado con respuesta y métricas
    """
    # Extraer pregunta
    question = state["messages"][-1].content if state["messages"] else None
    
    if not question:
        return {"messages": [AIMessage(content="No se encontró pregunta en el estado.")]}
    
    # Obtener contexto (puede estar vacío si no se usó RAG)
    context = state.get("context", "")
    
    # Decidir qué prompt usar según si hay contexto
    if context:
        # Usar prompt RAG
        prompt_text = rag_prompt.format(context=context, question=question)
    else:
        # Usar prompt simple
        prompt_text = ia_prompt.format(user_input=question)
    
    # Anteponer mensaje de sistema según modo (brief/extended)
    mode = str(state.get("mode", "extended")).lower()
    system_msg = get_system_message(mode)
    final_prompt = f"{system_msg}\n\n{prompt_text}"
    
    # Generar respuesta con métricas
    response_obj, llm_metrics = llm_instance.process_question(final_prompt, return_metrics=True)
    response_text = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
    
    # Si usamos RAG, calcular métricas adicionales
    result = {
        "messages": [AIMessage(content=response_text)],
        "user_question": question,      # Guardar pregunta
        "ai_response": response_text,   # Guardar respuesta
        **llm_metrics
    }
    
    if context:
        # Calcular métricas RAG (citaciones)
        rag_metrics = MetricsCollector.calculate_rag_metrics(context, response_text)
        result.update(rag_metrics)
        
        # Agregar metadata de fuentes
        sources_with_scores = state.get("sources_with_scores", [])
        sources = [s for s, _ in sources_with_scores]
        scores = [sc for _, sc in sources_with_scores]
        
        metadata = {
            "sources_with_scores": sources_with_scores,
            "sources": sources,
            "doc_ids": list(range(len(sources))),
            "similarity_scores": scores,
            "context_size": len(context),
            "num_retrieved_docs": len(sources)
        }
        
        # Actualizar el mensaje con metadata
        result["messages"] = [AIMessage(content=response_text, additional_kwargs=metadata)]
    
    return result


def metrics_node(state: MetricsState) -> dict:
    """
    Nodo de métricas: registra todas las métricas acumuladas en el CSV.
    
    Args:
        state: Estado actual del grafo con todas las métricas
        
    Returns:
        dict: Estado vacío (no modifica nada, solo registra)
    """
    # Obtener y limpiar pregunta y respuesta
    user_question = str(state.get("user_question", ""))
    ai_response = str(state.get("ai_response", ""))
    
    # Eliminar saltos de línea y normalizar espacios
    user_question_clean = " ".join(user_question.split())
    ai_response_clean = " ".join(ai_response.split())
    
    # Preparar datos para el logger
    log_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "thread_id": state.get("thread_id", ""),
        "user_question": user_question_clean,
        "ai_response": ai_response_clean,
        "latency_ms": f"{state.get('latency_ms', 0):.2f}",
        "input_tokens": state.get("input_tokens", 0),
        "output_tokens": state.get("output_tokens", 0),
        "total_tokens": state.get("total_tokens", 0),
        "estimated_cost_usd": f"{state.get('estimated_cost_usd', 0):.8f}",
        # Métricas RAG
        "num_retrieved_docs": state.get("num_retrieved_docs", 0),
        "context_size": state.get("context_size", 0),
        "avg_similarity_score": f"{state.get('avg_similarity_score', 0):.4f}",
        "citations_total": state.get("citations_total", 0),
        "citations_valid": state.get("citations_valid", 0),
        "citation_validity_ratio": f"{state.get('citation_validity_ratio', 0):.4f}",
        "hallucination_rate": f"{state.get('hallucination_rate', 0):.4f}"
    }
    
    # Registrar en CSV
    try:
        logger.log(log_data)
    except Exception as e:
        ic(f"Error al registrar métricas: {e}")
    
    # No modificar el estado
    return {}


def route_start(state: MetricsState) -> str:
    """
    Router: decide si pasar por RAG o ir directo a LLM.
    
    Args:
        state: Estado actual del grafo
        
    Returns:
        str: Nombre del siguiente nodo ("rag" o "llm")
    """
    if state.get("use_rag", False):
        return "rag"
    return "llm"
