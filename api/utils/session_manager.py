"""
Gestor común de sesiones para todas las plataformas.
Maneja sesiones de usuarios de forma unificada.
"""
import hashlib
import logging
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)

# Almacenamiento de sesiones (en producción usar Redis/DB)
# Estructura: {platform_user_hash: {opt_in: bool, mode: str, thread_id: str}}
sessions: Dict[str, Dict] = {}


def hash_user_id(platform: str, user_id: str) -> str:
    """
    Genera un hash anonimizado del ID de usuario.
    
    Args:
        platform: Nombre de la plataforma (whatsapp, telegram, etc.)
        user_id: ID del usuario en la plataforma
        
    Returns:
        str: Hash SHA256 del ID (primeros 16 caracteres)
    """
    combined = f"{platform}_{user_id}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def get_session(platform: str, user_id: str) -> Dict:
    """
    Obtiene o crea una sesión para un usuario en una plataforma.
    
    Args:
        platform: Nombre de la plataforma
        user_id: ID del usuario
        
    Returns:
        dict: Información de la sesión
    """
    session_hash = hash_user_id(platform, user_id)
    
    if session_hash not in sessions:
        sessions[session_hash] = {
            'platform': platform,
            'user_id': user_id,
            'opt_in': False,
            'mode': 'extended',
            'thread_id': f"{platform}_{session_hash}",
            'first_interaction': datetime.now().isoformat()
        }
    
    return sessions[session_hash]


def get_all_sessions() -> Dict:
    """Retorna todas las sesiones activas."""
    return sessions


def clear_session(platform: str, user_id: str) -> None:
    """
    Elimina una sesión específica.
    
    Args:
        platform: Nombre de la plataforma
        user_id: ID del usuario
    """
    session_hash = hash_user_id(platform, user_id)
    if session_hash in sessions:
        del sessions[session_hash]
        logger.info(f"Sesión eliminada: {platform}_{user_id}")


