import time
import csv
import os
import functools
from datetime import datetime

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
        self.metrics_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "metrics")
        os.makedirs(self.metrics_dir, exist_ok=True)
        
        # Construir la ruta completa del archivo
        self.filename = os.path.join(self.metrics_dir, filename)
        self.fieldnames = [
            "timestamp", 
            "latency_ms", 
            "input_tokens", 
            "output_tokens", 
            "total_tokens", 
            "estimated_cost_usd",
            "anonymized_question_len", # Log anonimizado
            "anonymized_response_len"  # Log anonimizado
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
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()

    def log(self, data):
        """
        Registra una nueva entrada de métricas en el archivo CSV.

        Args:
            data (dict): Diccionario con los datos a registrar. Debe contener
                        todas las claves definidas en self.fieldnames
        """
        with open(self.filename, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writerow(data)

# Instancia global del logger para que el decorador la use
# Esto creará un archivo 'ia_metrics_report.csv' en tu carpeta
logger = CsvMetricLogger()

def monitor_performance(func):
    """
    Decorador que monitorea y registra el rendimiento de las llamadas al LLM.

    Este decorador captura métricas importantes como:
    - Latencia de la llamada
    - Tokens de entrada y salida utilizados
    - Costo estimado de la operación
    - Longitud de preguntas y respuestas (anonimizado)

    Args:
        func (callable): Función a decorar. Debe ser un método de clase que procese
                        preguntas usando un LLM

    Returns:
        callable: Función decorada que incluye el monitoreo de rendimiento

    Note:
        La función decorada debe pertenecer a una clase que tenga los atributos
        self.llm y self.prompt configurados
    """
    @functools.wraps(func)
    def wrapper(self, question, *args, **kwargs):
        # 1. Medir Latencia
        start_time = time.perf_counter()
        
        # Ejecuta la función original (process_question)
        result_obj = func(self, question, *args, **kwargs)
        
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        try:
            # 2. Calcular Tokens (requiere acceso a self.llm y self.prompt)
            # Formatea el prompt completo tal como lo ve el LLM
            prompt_text = self.prompt.format(user_input=question)
            print()
            
            try:
                response_text = result_obj.content.strip()
            except Exception:
                response_text = str(result_obj).strip()

            usage = getattr(result_obj, "usage_metadata", None)
            if usage is not None:
                input_tokens = usage.get("input_tokens", None)
                output_tokens = usage.get("output_tokens", None)
                total_tokens = usage.get("total_tokens", None)
                # Si alguno es None, caemos al conteo manual
                if input_tokens is None or output_tokens is None or total_tokens is None:
                    raise ValueError("usage_metadata incompleta, usar método manual")
            else:
                raise ValueError("No se encontró usage_metadata, usar conteo manual")
            
        except Exception:
            # Conteo manual como respaldo
            input_tokens = self.llm.get_num_tokens(prompt_text)
            output_tokens = self.llm.get_num_tokens(response_text)
            total_tokens = input_tokens + output_tokens
            response_text = response_text  # ya lo tenemos

        # 3. Calcular Costo
        cost = (input_tokens / 1_000_000 * PRICE_INPUT_PER_MILLION) + \
               (output_tokens / 1_000_000 * PRICE_OUTPUT_PER_MILLION)
        
        # 4. Preparar Log Anonimizado
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "latency_ms": f"{latency_ms:.2f}",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": f"{cost:.8f}",
            "anonymized_question_len": len(question),
            "anonymized_response_len": len(response_text)
        }
        
        # 5. Escribir en el archivo CSV
        try:
            logger.log(log_data)
        except Exception as e:
            print(f"Error al registrar métricas en CSV: {e}")
        
        # Devuelve al usuario *sólo el texto* de la respuesta
        return response_text
    return wrapper
