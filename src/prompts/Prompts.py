"""Registro central de prompts para el chatbot.

Este módulo concentra todas las plantillas (prompts) usadas por el sistema
para que puedan ser reutilizadas, versionadas y auditadas fácilmente.

Características:
- Acceso estandarizado a prompts vía funciones helper
- Registro dinámico para agregar nuevos prompts en tiempo de ejecución
- Listado y recuperación de plantillas y objetos PromptTemplate

Uso básico:
    from src.prompts.prompt_registry import get_rag_prompt, get_ia_expert_prompt
    rag_prompt = get_rag_prompt()
    ia_prompt = get_ia_expert_prompt()
"""
from typing import Dict, List, Optional
from langchain_core.prompts import PromptTemplate

# =================== Plantillas Base (Strings) ===================
RAG_PROMPT_TEMPLATE: str = (
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

IA_EXPERT_PROMPT_TEMPLATE: str = (
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

# =================== Registro Dinámico ===================
# Cada entrada: nombre -> {"template": str, "input_variables": List[str]}
_prompt_registry: Dict[str, Dict[str, List[str]]] = {
    "rag": {"template": RAG_PROMPT_TEMPLATE, "input_variables": ["context", "question"]},
    "ia_expert": {"template": IA_EXPERT_PROMPT_TEMPLATE, "input_variables": ["user_input"]},
}

# =================== Helpers Específicos ===================
def get_rag_prompt() -> PromptTemplate:
    """Devuelve el PromptTemplate para RAG (context + question)."""
    data = _prompt_registry["rag"]
    return PromptTemplate(input_variables=data["input_variables"], template=data["template"])

def get_ia_expert_prompt(custom_template: Optional[str] = None) -> PromptTemplate:
    """Devuelve el PromptTemplate del asistente experto en IA.

    Args:
        custom_template: Si se pasa, reemplaza temporalmente el template base.
    """
    template = custom_template or _prompt_registry["ia_expert"]["template"]
    return PromptTemplate(input_variables=["user_input"], template=template)