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
    "Eres un asistente de IA. Responde la pregunta del usuario basándote "
    "en el siguiente contexto. Si el contexto no contiene la respuesta, "
    "intenta formar la respuesta con la mejor información disponible.\n\n"
    "IMPORTANTE - Cita tus fuentes usando el formato [nombre_archivo.txt] donde "
    "nombre_archivo.txt es EXACTAMENTE el nombre del documento que aparece después "
    "de 'Fuente X:' en el contexto. Ejemplo: si ves '[Fuente 1: documento.txt |...]', "
    "cita como [documento.txt], NUNCA LO PONGAS COMO [Fuente 1].\n\n"
    r"Si vas a poner la cita, NO lo pongas a formato de ruta, como data\new-docs\politica-nacional-transformacion-digital-ia.txt, "
    "Pon solo el nombre del archivo, en este caso sería politica-nacional-transformacion-digital-ia.txt.\n\n"
    "Solo usa nombres de archivos que aparezcan en el contexto.\n\n"
    "En el caso de que también se dé contexto de mensajes anteriores, responde con base en eso.\n\n"
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

# =================== Mensajes de Sistema (Modos) ===================
SYSTEM_BRIEF_PROMPT: str = (
    "[Sistema] Modo BREVE: Responde en 2-3 frases máximas, directas y prácticas. "
    "Evita florituras, solo lo esencial para resolver la pregunta."
)

SYSTEM_EXTENDED_PROMPT: str = (
    "[Sistema] Modo EXTENDIDO: Responde de forma desarrollada y pedagógica. "
    "Incluye definiciones clave, contexto necesario y, si aporta valor, ejemplos o pasos."
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

def get_system_message(mode: str = "extended") -> str:
    """Devuelve el mensaje de sistema según el modo deseado.

    Args:
        mode: "brief" o "extended" (cualquier otro valor cae en "extended").

    Returns:
        str: Mensaje del sistema a anteponer al prompt del usuario/RAG.
    """
    if str(mode).lower() == "brief":
        return SYSTEM_BRIEF_PROMPT
    return SYSTEM_EXTENDED_PROMPT