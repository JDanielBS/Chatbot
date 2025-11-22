import os
import time
from typing import Tuple, Union
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage

from src.prompts.Prompts import get_ia_expert_prompt
from src.metrics.Monitoring import monitor_performance, MetricsCollector

load_dotenv()

class IAExpertLLM:
    """
    Clase especializada en procesamiento de consultas sobre Inteligencia Artificial.
    
    Esta clase implementa un asistente experto en IA utilizando el modelo Gemini de Google.
    Proporciona capacidades para procesar preguntas relacionadas con conceptos de IA,
    historia, aplicaciones, y otros temas relacionados.

    Attributes:
        prompt (PromptTemplate): Template para formatear las preguntas del usuario
        llm (ChatGoogleGenerativeAI): Instancia del modelo de lenguaje de Google
        pipeline: Pipeline de procesamiento que combina el prompt y el modelo
    """

    def __init__(self, prompt_template: str | None = None):
        """
        Inicializa el asistente experto en IA.

        Args:
            prompt_template (str, optional): Template personalizado para el procesamiento de preguntas.
                                          Si no se proporciona, se usa un template predeterminado.
        """
        # Obtener el PromptTemplate desde el registro. Si se pasa uno personalizado, se aplica.
        self.prompt = get_ia_expert_prompt(custom_template=prompt_template)
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", api_key=os.getenv("GEMINI_API_KEY"))
        self.pipeline = self.prompt | self.llm

    def process_question(
        self, 
        question: str, 
        return_metrics: bool = False
    ) -> Union[str, Tuple[AIMessage, dict]]:
        """
        Procesa una pregunta y retorna un mensaje del asistente.
        
        Args:
            question (str): Pregunta del usuario
            return_metrics (bool): Si True, retorna también un dict con métricas
            
        Returns:
            str o Tuple[AIMessage, dict]: Texto de respuesta (si return_metrics=False)
                                          o tupla (AIMessage, métricas) (si return_metrics=True)
        """
        start_time = time.perf_counter()
        
        inputs = {"user_input": question}
        result = self.pipeline.invoke(inputs)
        
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        
        # Calcular métricas usando MetricsCollector
        prompt_text = self.prompt.format(user_input=question)
        metrics = MetricsCollector.calculate_llm_metrics(
            llm_instance=self.llm,
            prompt_text=prompt_text,
            response_obj=result,
            latency_ms=latency_ms,
            question=question
        )

        return result, metrics
