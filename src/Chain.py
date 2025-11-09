from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from icecream import ic

from .RAG_manager import RAGManager

class IAChain():
    def __init__(self, llm, rag: RAGManager):
        """
        Inicializa la cadena de IA con memoria persistente.
        """
        self.llm = llm
        self.memory = MemorySaver()
        self.rag = rag
        self.graph = self._build_graph()

        # Plantilla de prompt para RAG
        self.rag_prompt_template = (
            "Eres un asistente de IA. Responde la pregunta del usuario basándote ÚNICAMENTE "
            "en el siguiente contexto. Si el contexto no contiene la respuesta, "
            "indica que no tienes esa información.\n"
            "Cita tus fuentes usando el formato [Fuente X] al final de la oración o párrafo "
            "correspondiente, donde X es el número de la fuente.\n\n"
            "Contexto:\n"
            "{context}\n\n"
            "Pregunta: {question}\n\n"
            "Respuesta:"
        )
        self.rag_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=self.rag_prompt_template
        )

    def _build_graph(self) -> StateGraph:
        """Construye el grafo de estados para el procesamiento de mensajes."""
        builder = StateGraph(MessagesState)

        builder.add_node("assistant", self.assistant)
        builder.add_node("rag", self.rag_node)
        """ builder.add_edge(START, "assistant")
        builder.add_edge("assistant", END) """

        builder.add_edge(START, "rag")
        builder.add_edge("rag", END)

        return builder.compile(checkpointer=self.memory)
    
    def assistant(self, state: MessagesState):
        """Nodo asistente simple sin RAG"""
        return {"messages": [self.llm.process_question(state["messages"])]}
    
    def rag_node(self, state: MessagesState):
        """
        Nodo RAG que devuelve respuesta y metadatos para métricas.
        """
        # 1. Extraer pregunta del estado
        question = None
        for msg in state["messages"]:
            if isinstance(msg, HumanMessage):
                question = msg.content
                break
        
        if not question:
            return {"messages": [AIMessage(content="No se encontró pregunta en el estado.", additional_kwargs={})]}
        
        # 2. Recuperar contexto y fuentes mediante el nuevo método MMR
        context, sources_with_scores = self.rag.build_context(question, k=6)

        # 3. Extraer metadatos estructurados
        sources = [s for s, _ in sources_with_scores]
        scores = [sc for _, sc in sources_with_scores]
        doc_ids = list(range(len(sources)))

        # 4. Construir el prompt e invocar el LLM
        prompt_text = self.rag_prompt.format(context=context, question=question)
        response_text = self.llm.process_question(prompt_text)

        # 5. Empaquetar metadatos para trazabilidad y métricas
        metadata = {
            "sources": sources,
            "doc_ids": doc_ids,
            "similarity_scores": scores,
            "context_size": len(context),
            "num_retrieved_docs": len(sources)
        }

        return {"messages": [AIMessage(content=response_text, additional_kwargs=metadata)]}

    
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
