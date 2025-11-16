"""
Sistema de logging anonimizado para WhatsApp.

Este módulo guarda métricas de interacción sin información personal identificable (PII).
"""

import os
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

LOGS_DIR = Path("./metrics/whatsapp_logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOGS_DIR / "whatsapp_interactions.csv"

CSV_HEADERS = [
    'timestamp',
    'session_hash',
    'message_length',
    'response_length',
    'mode',
    'query_number',
    'sources_found'
]


def log_interaction(
    session_hash: str,
    message_length: int,
    response_length: int,
    mode: str,
    query_number: int,
    sources_found: int = 0
) -> None:
    """
    Registra una interacción de forma anonimizada (sin PII).
    
    Args:
        session_hash: Hash anonimizado del número de teléfono
        message_length: Longitud del mensaje (sin guardar el texto)
        response_length: Longitud de la respuesta
        mode: Modo usado (brief/extended)
        query_number: Número de consulta global
        sources_found: Número de fuentes encontradas
    """
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'session_hash': session_hash,
        'message_length': message_length,
        'response_length': response_length,
        'mode': mode,
        'query_number': query_number,
        'sources_found': sources_found
    }
    
    file_exists = LOG_FILE.exists()
    
    try:
        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            
            # Escribir headers si es la primera vez
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(log_entry)
    
    except Exception as e:
        print(f"Error escribiendo log: {e}")


def get_logs_summary() -> Dict[str, Any]:
    """
    Obtiene un resumen de los logs (sin PII).
    
    Returns:
        dict: Resumen estadístico de las interacciones
    """
    if not LOG_FILE.exists():
        return {
            'total_interactions': 0,
            'total_sessions': 0,
            'modes_usage': {},
            'avg_response_length': 0
        }
    
    try:
        sessions = set()
        interactions = 0
        total_response_length = 0
        modes_count = {}
        
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                interactions += 1
                sessions.add(row['session_hash'])
                total_response_length += int(row.get('response_length', 0))
                
                mode = row.get('mode', 'unknown')
                modes_count[mode] = modes_count.get(mode, 0) + 1
        
        return {
            'total_interactions': interactions,
            'total_sessions': len(sessions),
            'modes_usage': modes_count,
            'avg_response_length': total_response_length / interactions if interactions > 0 else 0
        }
    
    except Exception as e:
        print(f"Error leyendo logs: {e}")
        return {
            'total_interactions': 0,
            'total_sessions': 0,
            'modes_usage': {},
            'avg_response_length': 0
        }

