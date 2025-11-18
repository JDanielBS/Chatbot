import json
import os
from pathlib import Path
from typing import Dict, List

def load_sources_metadata() -> Dict[str, Dict[str, str]]:
    """
    Carga el archivo JSON con metadata de las fuentes.
    
    Returns:
        Dict con estructura: {filename: {"title": str, "author": str}}
    """
    base_path = Path(__file__).parent.parent.parent
    metadata_path = base_path / "data" / "sources_metadata.json"
    
    if not metadata_path.exists():
        return {}
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando metadata de fuentes: {e}")
        return {}


def get_all_sources_display() -> List[str]:
    """
    Obtiene todas las fuentes en formato "Título - Autor".
    
    Returns:
        List[str]: Lista de fuentes formateadas
    """
    metadata = load_sources_metadata()
    sources_list = []
    
    for filename, info in metadata.items():
        title = info.get("title", filename)
        author = info.get("author", "")
        
        if author:
            display_name = f"{title} - {author}"
        else:
            display_name = title
        
        sources_list.append(display_name)
    
    return sorted(sources_list)

