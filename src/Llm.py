import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

from src.Monitoring import monitor_performance

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

    def __init__(self, prompt_template=None):
        """
        Inicializa el asistente experto en IA.

        Args:
            prompt_template (str, optional): Template personalizado para el procesamiento de preguntas.
                                          Si no se proporciona, se usa un template predeterminado.
        """
        if prompt_template is None:
            prompt_template = (
                "Eres un asistente experto en Inteligencia Artificial, con amplio conocimiento en:\n"
                "- Conceptos fundamentales de IA\n"
                "- Historia y evolución de la IA\n"
                "- Tipos de IA (débil, fuerte, AGI)\n"
                "- Machine Learning y Deep Learning\n"
                "- Aplicaciones prácticas de IA\n"
                "- Ética en IA y consideraciones sociales\n"
                "- Tendencias y avances actuales\n\n"
                "Responde de manera clara, precisa y educativa a la siguiente pregunta: {user_input}\n"
                "Si no estás seguro de algo, indícalo. Mantén las respuestas concisas pero informativas."
            )
        
        self.prompt = PromptTemplate(
            input_variables=["user_input"],
            template=prompt_template
        )
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", api_key=os.getenv("GEMINI_API_KEY"))
        self.pipeline = self.prompt | self.llm

    @monitor_performance
    def process_question(self, question: str) -> str:
        """
        Procesa una pregunta sobre IA y retorna la respuesta generada.

        Args:
            question (str): Pregunta del usuario sobre IA que se desea procesar

        Returns:
            str: Respuesta generada por el modelo a la pregunta formulada

        Note:
            Este método está decorado con @monitor_performance para seguimiento de métricas
        """
        inputs = {"user_input": question}
        result = self.pipeline.invoke(inputs)
        return result

    def get_prompt_template(self) -> str:
        """
        Obtiene el template actual del prompt.

        Returns:
            str: Template actual usado para formatear las preguntas
        """
        return self.prompt.template

    def set_prompt_template(self, new_template: str):
        """
        Actualiza el template del prompt usado para procesar preguntas.

        Args:
            new_template (str): Nuevo template que reemplazará al actual.
                              Debe incluir la variable {user_input}
        """
        self.prompt = PromptTemplate(
            input_variables=["user_input"],
            template=new_template
        )
        self.pipeline = self.prompt | self.llm
