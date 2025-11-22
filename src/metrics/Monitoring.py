import time
import csv
import os
import functools
import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# --- INICIO DE LA SOLUCIÓN DE MONITOREO ---

# Define aquí los precios por 1 MILLÓN de tokens para tu modelo.
# Estos son para 'gemini-2.0-flash' (USD)
PRICE_INPUT_PER_MILLION = 0.10
PRICE_OUTPUT_PER_MILLION = 0.40

class CsvMetricLogger:
    """
    Clase para registrar métricas de rendimiento del LLM en archivos CSV.

    Esta clase maneja la creación y actualización de archivos CSV que contienen
    métricas de rendimiento como latencia, uso de tokens y costos estimados
    de las consultas al modelo de lenguaje.

    Attributes:
        metrics_dir (str): Ruta al directorio donde se almacenan las métricas
        filename (str): Ruta completa al archivo CSV de métricas
        fieldnames (list): Lista de columnas que se registrarán en el CSV
    """

    def __init__(self, filename="ia_metrics_report.csv"):
        """
        Inicializa el logger de métricas.

        Args:
            filename (str): Nombre del archivo CSV donde se guardarán las métricas.
                            Por defecto es 'ia_metrics_report.csv'
        """
        # Crear el directorio metrics si no existe
        self.metrics_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "metrics")
        os.makedirs(self.metrics_dir, exist_ok=True)
        
        # Construir la ruta completa del archivo
        self.filename = os.path.join(self.metrics_dir, filename)
        self.fieldnames = [
            "timestamp", 
            "thread_id",
            "user_question",      # Pregunta del usuario
            "ai_response",        # Respuesta de la IA
            "latency_ms", 
            "input_tokens", 
            "output_tokens", 
            "total_tokens", 
            "estimated_cost_usd",
            # Métricas RAG
            "num_retrieved_docs",
            "context_size",
            "avg_similarity_score",
            "citations_total",
            "citations_valid",
            "citation_validity_ratio",
            "hallucination_rate"
        ]
        self._initialize_file()

    def _initialize_file(self):
        """
        Inicializa el archivo CSV si no existe.

        Crea el archivo CSV con los encabezados correspondientes si no existe.
        Este método es privado y solo se usa internamente.
        """
        file_exists = os.path.isfile(self.filename)
        if not file_exists:
            with open(self.filename, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames, quoting=csv.QUOTE_ALL)
                writer.writeheader()

    def log(self, data):
        """
        Registra una nueva entrada de métricas en el archivo CSV.

        Args:
            data (dict): Diccionario con los datos a registrar. Debe contener
                        todas las claves definidas en self.fieldnames
        
        Note:
            Usa QUOTE_ALL para asegurar que strings complejos (con saltos de línea,
            comas, comillas) se escapen correctamente en el CSV.
        """
        with open(self.filename, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames, quoting=csv.QUOTE_ALL)
            writer.writerow(data)

# Instancia global del logger para que el decorador la use
# Esto creará un archivo 'ia_metrics_report.csv' en tu carpeta
logger = CsvMetricLogger()


class MetricsCollector:
    """
    Clase para recolectar métricas de rendimiento del LLM sin usar decoradores.
    
    Permite calcular métricas de latencia, tokens, costos y RAG que pueden
    acumularse en el estado del grafo y registrarse al final de la ejecución.
    """
    
    @staticmethod
    def calculate_llm_metrics(
        llm_instance,
        prompt_text: str,
        response_obj,
        latency_ms: float,
        question: str
    ) -> Dict[str, Any]:
        """
        Calcula métricas de rendimiento del LLM.
        
        Args:
            llm_instance: Instancia del LLM (para conteo de tokens manual si es necesario)
            prompt_text: Texto del prompt completo formateado
            response_obj: Objeto de respuesta del LLM
            latency_ms: Latencia medida en milisegundos
            question: Pregunta original del usuario
            
        Returns:
            Dict con métricas: input_tokens, output_tokens, total_tokens, 
                              estimated_cost_usd, latency_ms, question_len, response_len
        """
        try:
            response_text = response_obj.content.strip()
        except Exception:
            response_text = str(response_obj).strip()

        # Intentar obtener métricas de uso
        usage = getattr(response_obj, "usage_metadata", None)
        if usage is not None:
            input_tokens = usage.get("input_tokens", None)
            output_tokens = usage.get("output_tokens", None)
            total_tokens = usage.get("total_tokens", None)
            
            if input_tokens is None or output_tokens is None or total_tokens is None:
                # Conteo manual como respaldo
                input_tokens = llm_instance.get_num_tokens(prompt_text)
                output_tokens = llm_instance.get_num_tokens(response_text)
                total_tokens = input_tokens + output_tokens
        else:
            # Conteo manual
            input_tokens = llm_instance.get_num_tokens(prompt_text)
            output_tokens = llm_instance.get_num_tokens(response_text)
            total_tokens = input_tokens + output_tokens
        
        # Calcular costo
        cost = (input_tokens / 1_000_000 * PRICE_INPUT_PER_MILLION) + \
               (output_tokens / 1_000_000 * PRICE_OUTPUT_PER_MILLION)
        
        return {
            "latency_ms": latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": cost
        }
    
    @staticmethod
    def calculate_rag_metrics(context: str, response_text: str) -> Dict[str, Any]:
        """
        Calcula métricas relacionadas con RAG (citaciones y alucinaciones).
        
        Detecta citaciones usando el patrón [cualquier_cadena.txt] en la respuesta
        y valida que esos archivos existan en el contexto proporcionado.
        
        Args:
            context: Contexto proporcionado al LLM
            response_text: Respuesta generada por el LLM
            
        Returns:
            Dict con métricas: citations_total, citations_valid, 
                              citation_validity_ratio, hallucination_rate
        """
        # Detectar citaciones en formato [nombre_archivo.txt] (cualquier extensión)
        citation_pattern = r'\[([^\[\]]+\.(?:txt|pdf|docx?|md))\]'
        citations_found = re.findall(citation_pattern, response_text, re.IGNORECASE)
        citations_total = len(citations_found)
        
        # Extraer rutas completas del contexto (formato [Fuente X: ruta\archivo.txt] ...)
        context_source_pattern = r'\[Fuente\s+\d+:\s+([^\]]+?\.(?:txt|pdf|docx?|md))\]'
        context_sources_full_paths = re.findall(context_source_pattern, context, re.IGNORECASE)
        
        # Extraer solo los nombres de archivo (última parte después de \ o /)
        valid_source_names = set()
        for full_path in context_sources_full_paths:
            # Normalizar separadores y obtener el nombre del archivo
            filename = full_path.replace('/', '\\').split('\\')[-1].strip()
            valid_source_names.add(filename)
        
        # Contar citaciones válidas (el archivo citado existe en el contexto)
        citations_valid = sum(1 for cited_file in citations_found if cited_file.strip() in valid_source_names)
        
        # Ratio de validez de citaciones
        citation_validity_ratio = citations_valid / citations_total if citations_total > 0 else 1.0
        
        # Estimación simple de alucinación: citaciones inválidas / total
        hallucination_rate = 1.0 - citation_validity_ratio if citations_total > 0 else 0.0
        
        return {
            "citations_total": citations_total,
            "citations_valid": citations_valid,
            "citation_validity_ratio": citation_validity_ratio,
            "hallucination_rate": hallucination_rate
        }
    
    @staticmethod
    def calculate_retrieval_metrics(
        sources_with_scores: list,
        context: str
    ) -> Dict[str, Any]:
        """
        Calcula métricas de recuperación de documentos.
        
        Args:
            sources_with_scores: Lista de tuplas (source, score)
            context: Contexto construido
            
        Returns:
            Dict con métricas: num_retrieved_docs, context_size, avg_similarity_score
        """
        scores = [score for _, score in sources_with_scores]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "num_retrieved_docs": len(sources_with_scores),
            "context_size": len(context),
            "avg_similarity_score": avg_score
        }


def compute_rag_metrics(context: str, response_text: str) -> Dict[str, Any]:
    """
    Función de compatibilidad que utiliza MetricsCollector.
    
    Args:
        context: Contexto proporcionado
        response_text: Respuesta generada
        
    Returns:
        Dict con métricas RAG
    """
    return MetricsCollector.calculate_rag_metrics(context, response_text)
