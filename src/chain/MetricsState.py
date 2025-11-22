from typing import TypedDict, Annotated, Optional
import operator

class MetricsState(TypedDict, total=False):
    """Estado extendido que incluye campos para acumular métricas durante la ejecución del grafo."""
    # Campos heredados de MessagesState
    messages: Annotated[list, operator.add]
    
    # Campos RAG
    context: Optional[str]
    sources_with_scores: Optional[list]
    use_rag: Optional[bool]  # Flag para controlar si se usa RAG
    mode: Optional[str]  # Modo de respuesta: "brief" o "extended"
    
    # Campos de métricas que se van acumulando
    thread_id: Optional[str]
    user_question: Optional[str]  # Pregunta del usuario
    ai_response: Optional[str]    # Respuesta de la IA
    latency_ms: Optional[float]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    total_tokens: Optional[int]
    estimated_cost_usd: Optional[float]
    
    # Métricas RAG
    num_retrieved_docs: Optional[int]
    context_size: Optional[int]
    avg_similarity_score: Optional[float]
    citations_total: Optional[int]
    citations_valid: Optional[int]
    citation_validity_ratio: Optional[float]
    hallucination_rate: Optional[float]
    
    # Control de tiempo
    start_time: Optional[float]