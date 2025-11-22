"""
Test suite para evaluar el chatbot con las preguntas gold standard.

Este módulo ejecuta pruebas automatizadas usando las preguntas de referencia
almacenadas en data/gold_questions/preguntas_gold.txt y registra los resultados
en un archivo JSON para análisis posterior.
"""
import unittest
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
import sys, pathlib

# Inserta la carpeta raíz (que contiene 'src') al inicio del sys.path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Importaciones necesarias del proyecto
from src.llm.RAG_manager import RAGManager
from src.llm.Llm import IAExpertLLM
from src.chain.Chain import IAChain


class TestGoldQuestions(unittest.TestCase):
    """
    Clase de pruebas para evaluar el chatbot con preguntas gold standard.
    
    Esta clase carga las preguntas de referencia, ejecuta el chatbot para cada una
    y guarda los resultados (pregunta, respuesta, metadata) en un archivo JSON.
    """
    
    @classmethod
    def setUpClass(cls):
        """
        Configuración inicial para todas las pruebas.
        
        Inicializa el LLM, RAG y la cadena de LangChain que se usarán
        en todas las pruebas.
        """
        print("\n" + "="*80)
        print("Inicializando sistema de IA para pruebas con preguntas gold...")
        print("="*80)
        
        cls.ia_llm = IAExpertLLM()
        cls.rag = RAGManager()
        cls.chain = IAChain(cls.ia_llm, cls.rag)
        
        # Rutas de archivos
        project_root = Path(__file__).parent.parent
        cls.gold_questions_path = project_root / "data" / "gold_questions" / "preguntas_gold.txt"
        cls.results_path = project_root / "metrics" / "gold_questions_results.json"
        
        # Cargar preguntas
        cls.questions = cls.load_gold_questions()
        print(f"\n✓ Cargadas {len(cls.questions)} preguntas gold")
        print(f"✓ Resultados se guardarán en: {cls.results_path}")
        print("="*80 + "\n")
    
    @classmethod
    def load_gold_questions(cls) -> list:
        """
        Carga las preguntas gold desde el archivo de texto.
        
        Lee el archivo preguntas_gold.txt y divide las preguntas por saltos de línea,
        filtrando líneas vacías.
        
        Returns:
            list: Lista de preguntas (strings no vacíos)
        """
        if not cls.gold_questions_path.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo de preguntas gold en: {cls.gold_questions_path}"
            )
        
        with open(cls.gold_questions_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Dividir por saltos de línea y filtrar líneas vacías
        questions = [q.strip() for q in content.split('\n') if q.strip()]
        
        return questions
    
    def test_all_gold_questions(self):
        """
        Ejecuta el chatbot con todas las preguntas gold y guarda los resultados.
        
        Para cada pregunta:
        1. Genera un thread_id único
        2. Invoca la cadena de LangChain
        3. Guarda pregunta, respuesta y metadata en JSON
        """
        results = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "total_questions": len(self.questions),
                "test_description": "Evaluación con preguntas gold standard"
            },
            "results": []
        }
        
        print("\nIniciando evaluación de preguntas gold...\n")
        
        for idx, question in enumerate(self.questions, start=1):
            print(f"[{idx}/{len(self.questions)}] Procesando pregunta...")
            print(f"Pregunta: {question[:100]}{'...' if len(question) > 100 else ''}")
            
            # Generar thread_id único para cada pregunta
            thread_id = str(uuid.uuid4())
            
            try:
                # Invocar la cadena con la pregunta
                response, metadata = self.chain.invoke(
                    inputs=question,
                    thread_id=thread_id,
                    use_rag=True,
                    return_metadata=True,
                    mode="extended"
                )
                
                # Guardar resultado
                result_entry = {
                    "question_number": idx,
                    "thread_id": thread_id,
                    "question": question,
                    "response": response,
                    "metadata": metadata,
                    "status": "success"
                }
                
                print(f"✓ Respuesta generada ({len(response)} caracteres)")
                print(f"✓ Métricas: {metadata.get('latency_ms', 'N/A')}ms, "
                      f"{metadata.get('total_tokens', 'N/A')} tokens")
                
            except Exception as e:
                # Capturar errores y continuar con la siguiente pregunta
                result_entry = {
                    "question_number": idx,
                    "thread_id": thread_id,
                    "question": question,
                    "response": None,
                    "metadata": None,
                    "status": "error",
                    "error_message": str(e)
                }
                
                print(f"✗ Error al procesar pregunta: {str(e)}")
            
            results["results"].append(result_entry)
            print("-" * 80 + "\n")
        
        # Guardar todos los resultados en JSON
        self.save_results(results)
        
        # Verificar que se procesaron todas las preguntas
        self.assertEqual(
            len(results["results"]),
            len(self.questions),
            "No se procesaron todas las preguntas"
        )
        
        # Contar éxitos y errores
        successful = sum(1 for r in results["results"] if r["status"] == "success")
        failed = sum(1 for r in results["results"] if r["status"] == "error")
        
        print("\n" + "="*80)
        print("RESUMEN DE EVALUACIÓN")
        print("="*80)
        print(f"Total de preguntas: {len(self.questions)}")
        print(f"Exitosas: {successful}")
        print(f"Fallidas: {failed}")
        print(f"Tasa de éxito: {(successful/len(self.questions)*100):.2f}%")
        print(f"\nResultados guardados en: {self.results_path}")
        print("="*80 + "\n")
    
    def save_results(self, results: dict):
        """
        Guarda los resultados en un archivo JSON.
        
        Args:
            results (dict): Diccionario con toda la información de resultados
        """
        # Asegurar que el directorio existe
        self.results_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Guardar con formato legible
        with open(self.results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    # Ejecutar las pruebas
    unittest.main(verbosity=2)
