from typing import Dict
from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

class IAChain:
    def __init__(self, llm):
        """
        Inicializa la cadena de IA con memoria persistente.
        """
        self.llm = llm
        self.memory = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Construye el grafo de estados para el procesamiento de mensajes."""
        builder = StateGraph(MessagesState)

        builder.add_node("assistant", self.assistant)
        builder.add_edge(START, "assistant")
        builder.add_edge("assistant", END)

        return builder.compile(checkpointer=self.memory)
    
    def assistant(self, state: MessagesState):
        return {"messages": [self.llm.process_question(state["messages"])]}
    
    def invoke(self, inputs, thread_id) -> str:
        """
        Invoca la cadena con los inputs proporcionados.

        Args:
            inputs (Dict): Diccionario con los inputs necesarios para la cadena.
            thread_id (str): ID único de la conversación

        Returns:
            str: Texto de la respuesta generada por el modelo
        """
        message = [HumanMessage(content=str(inputs))]
        config = {"configurable": {"thread_id": thread_id}}
        
        result = self.graph.invoke({"messages": message}, config)
        response = result["messages"][-1]
        
        # Extraer el contenido del mensaje
        if hasattr(response, 'content'):
            return response.content
        return str(response)
