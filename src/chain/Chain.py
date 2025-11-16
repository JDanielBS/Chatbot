from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
import time
from icecream import ic

from src.llm.RAG_manager import RAGManager
from src.chain.MetricsState import MetricsState
from src.prompts.Prompts import get_rag_prompt, get_ia_expert_prompt
from src.chain.Nodes import rag_node, llm_node, metrics_node, route_start


class IAChain():
    def __init__(self, llm, rag: RAGManager):
        """
        Inicializa la cadena de IA con memoria persistente.
        
        Args:
            llm: Instancia del modelo de lenguaje
            rag: Instancia del gestor RAG
        """
        self.llm = llm
        self.rag = rag
        self.memory = MemorySaver()
        
        # Prompts centralizados
        self.rag_prompt = get_rag_prompt()
        self.ia_prompt = get_ia_expert_prompt()
        
        # Construir el grafo
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Construye el grafo de estados para el procesamiento de mensajes."""
        builder = StateGraph(MetricsState)
        
        # Agregar nodos (usando lambdas para pasar las dependencias)
        builder.add_node("rag", lambda state: rag_node(state, self.rag))
        builder.add_node("llm", lambda state: llm_node(state, self.llm, self.rag_prompt, self.ia_prompt))
        builder.add_node("metrics", lambda state: metrics_node(state))
        
        # Flujo condicional desde START
        builder.add_conditional_edges(START, route_start, {"rag": "rag", "llm": "llm"})
        builder.add_edge("rag", "llm")
        builder.add_edge("llm", "metrics")
        builder.add_edge("metrics", END)
        
        return builder.compile(checkpointer=self.memory)
    
    def invoke(self, inputs, thread_id, use_rag: bool = False, return_metadata: bool = False):
        """
        Invoca la cadena con los inputs proporcionados.

        Args:
            inputs: Pregunta del usuario (str)
            thread_id: ID único de la conversación
            use_rag: Si True, usa el nodo RAG para recuperar contexto
            return_metadata: Si True, retorna también los metadatos

        Returns:
            str o Tuple[str, dict]: Respuesta generada, opcionalmente con metadatos
        """
        # Preparar mensaje y configuración
        message = [HumanMessage(content=str(inputs))]
        config = {"configurable": {"thread_id": thread_id}}
        
        # Inicializar estado
        initial_state = {
            "messages": message,
            "thread_id": thread_id,
            "use_rag": use_rag,
            "start_time": time.perf_counter()
        }
        
        # Invocar el grafo
        result = self.graph.invoke(initial_state, config)
        
        # Extraer respuesta
        response = result["messages"][-1]
        response_text = response.content if hasattr(response, 'content') else str(response)
        metadata = getattr(response, 'additional_kwargs', {}) or {}
        
        if return_metadata:
            return response_text, metadata
        return response_text
