"""
Configuración de mensajes comunes para todas las plataformas.
Todos los mensajes son parametrizables y fáciles de modificar.
"""
from typing import List

# ============================================================================
# CONFIGURACIÓN DE INSTITUCIÓN
# ============================================================================

INSTITUTION_NAME = "Universidad de Caldas"
BOT_NAME = "Chatbot de Inteligencia Artificial"

# ============================================================================
# MENSAJES PRINCIPALES
# ============================================================================

# Mensaje de bienvenida (texto plano, sin formato de plataforma)
WELCOME_MESSAGE_TEMPLATE = """Bienvenido al {bot_name}

Soy un asistente especializado en Inteligencia Artificial de la {institution}.

Política de Privacidad:
• No almacenamos información personal
• Solo registramos métricas anónimas para mejorar el servicio
• Tus conversaciones son privadas y seguras

Para continuar:
Responde ACEPTO para usar el servicio, o SALIR si no deseas continuar.

Comandos disponibles:
• POLÍTICA - Ver política de uso completa
• FUENTE(S) - Ver fuentes confiables utilizadas
• MODO BREVE - Respuestas cortas (2-3 frases)
• MODO EXTENDIDO - Respuestas detalladas con citas
• SALIR - Dejar de usar el servicio"""

# Mensaje de política
POLICY_MESSAGE_TEMPLATE = """Política de Uso del Chatbot

¿Qué es este bot?
Soy un asistente de IA especializado en Inteligencia Artificial, desarrollado por la {institution}.

Privacidad:
• No almacenamos tu número de teléfono ni información personal
• Solo guardamos métricas anónimas (tiempo de respuesta, tipo de pregunta, etc.)
• Cada sesión tiene un ID único anonimizado

Opt-in/Opt-out:
• Debes aceptar explícitamente para usar el servicio (escribe "ACEPTO")
• Puedes salir en cualquier momento escribiendo "SALIR"
• Al salir, tu sesión se cierra y no recibirás más respuestas

Uso de datos:
• Las métricas se usan solo para mejorar el servicio
• No compartimos información con terceros
• Cumplimos con normativas de protección de datos

Fuentes:
El bot utiliza documentos académicos confiables sobre IA. Escribe "FUENTE(S)" para ver la lista completa.

¿Tienes más preguntas? Escribe cualquier pregunta sobre IA y te ayudaré."""

# ============================================================================
# MENSAJES DE COMANDOS
# ============================================================================

COMMAND_MESSAGES = {
    "mode_brief_activated": "✅ Modo Breve activado\n\nAhora recibirás respuestas cortas y concisas (2-3 frases).\n\nEscribe 'MODO EXTENDIDO' para cambiar.",
    "mode_extended_activated": "✅ Modo Extendido activado\n\nAhora recibirás respuestas detalladas con explicaciones y citas.\n\nEscribe 'MODO BREVE' para cambiar.",
    "opt_in_success": "✅ ¡Bienvenido!\n\nAhora puedes hacer preguntas sobre Inteligencia Artificial.\n\nComandos disponibles:\n• POLÍTICA - Ver política\n• FUENTE(S) - Ver fuentes\n• MODO BREVE/EXTENDIDO - Cambiar modo\n• SALIR - Salir del servicio",
    "opt_out_success": "👋 Sesión cerrada\n\nHas salido del servicio. No recibirás más respuestas.\n\nPara volver a usar el bot, escribe 'ACEPTO'.",
    "image_received": "📸 Recibí tu imagen. Por ahora solo puedo responder mensajes de texto sobre Inteligencia Artificial.",
    "audio_received": "🎤 Recibí tu audio. Por ahora solo puedo responder mensajes de texto sobre Inteligencia Artificial.",
    "video_received": "🎥 Recibí tu video. Por ahora solo puedo responder mensajes de texto sobre Inteligencia Artificial.",
    "document_received": "📄 Recibí tu documento. Por ahora solo puedo responder mensajes de texto sobre Inteligencia Artificial.",
    "error_processing": "❌ Lo siento, tuve un problema al procesar tu mensaje. ¿Podrías intentarlo de nuevo?",
    "error_sources": "❌ No pude obtener la lista de fuentes en este momento. Por favor intenta más tarde."
}

# Mensaje de error para fuentes
SOURCES_ERROR_MESSAGE = """❌ Error al obtener fuentes

No pude acceder a la base de datos de documentos en este momento.

El bot utiliza documentos académicos y normativos sobre Inteligencia Artificial de organizaciones como UNESCO, la Comisión Europea y fuentes académicas reconocidas.

Por favor intenta más tarde o contacta al administrador."""

# ============================================================================
# FUNCIONES DE FORMATO
# ============================================================================

def get_welcome_message() -> str:
    """
    Retorna el mensaje de bienvenida formateado.
    
    Returns:
        str: Mensaje de bienvenida con variables reemplazadas
    """
    return WELCOME_MESSAGE_TEMPLATE.format(
        bot_name=BOT_NAME,
        institution=INSTITUTION_NAME
    )


def get_policy_message() -> str:
    """
    Retorna el mensaje de política formateado.
    
    Returns:
        str: Mensaje de política con variables reemplazadas
    """
    return POLICY_MESSAGE_TEMPLATE.format(institution=INSTITUTION_NAME)


def get_command_message(key: str) -> str:
    """
    Obtiene un mensaje de comando por su clave.
    
    Args:
        key: Clave del mensaje en COMMAND_MESSAGES
        
    Returns:
        str: Mensaje correspondiente o cadena vacía si no existe
    """
    return COMMAND_MESSAGES.get(key, "")


def format_sources_message(sources_list: List[str], total_chunks: int, error: bool = False) -> str:
    """
    Formatea el mensaje de fuentes.
    
    Args:
        sources_list: Lista de nombres de fuentes (formato "• nombre")
        total_chunks: Total de chunks indexados
        error: Si hubo un error al obtener las fuentes
        
    Returns:
        str: Mensaje formateado
    """
    if error:
        return SOURCES_ERROR_MESSAGE
    
    if not sources_list:
        return SOURCES_ERROR_MESSAGE
    
    message = "Fuentes Confiables Utilizadas:\n\n"
    message += "\n".join(sources_list[:15])  # Limitar a 15
    
    if len(sources_list) > 15:
        message += f"\n\n... y {len(sources_list) - 15} documentos más"
    
    message += f"\n\nTotal de chunks indexados: {total_chunks}"
    message += "\n\nEstas fuentes se utilizan para proporcionar respuestas precisas y actualizadas sobre Inteligencia Artificial."
    
    return message


# ============================================================================
# FORMATEADORES POR PLATAFORMA
# ============================================================================

def format_for_whatsapp(message: str) -> str:
    """
    Formatea mensaje para WhatsApp (soporta Markdown básico).
    
    Args:
        message: Mensaje en texto plano
        
    Returns:
        str: Mensaje formateado para WhatsApp
    """
    # WhatsApp soporta *negrita* y _cursiva_
    # Ya está en el formato correcto, solo retornamos
    return message


def format_for_telegram(message: str) -> str:
    """
    Formatea mensaje para Telegram (soporta Markdown).
    
    Args:
        message: Mensaje en texto plano
        
    Returns:
        str: Mensaje formateado para Telegram
    """
    # Telegram soporta Markdown similar
    # Ya está en el formato correcto, solo retornamos
    return message


