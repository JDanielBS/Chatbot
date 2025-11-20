"""
Sistema de logging anonimizado para todas las plataformas.
Guarda métricas de interacción sin información personal identificable 
"""
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

LOGS_DIR = Path("./metrics/message_logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOGS_DIR / "interactions.csv"

CSV_HEADERS = [
    'timestamp',
    'platform',
    'session_hash',
    'message_length',
    'response_length',
    'mode',
    'query_number',
    'sources_found'
]


def log_interaction(
    session_hash: str,
    platform: str,
    message_length: int,
    response_length: int,
    mode: str,
    query_number: int,
    sources_found: int = 0
) -> None:
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'platform': platform,
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
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(log_entry)
    
    except Exception as e:
        print(f"Error escribiendo log: {e}")