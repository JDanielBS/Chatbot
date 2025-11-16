from src.llm.RAG_manager import RAGManager
from src.llm.Llm import IAExpertLLM
from src.chain.Chain import IAChain
import uuid

def main():
    # Inicializar el LLM y la cadena
    ia_llm = IAExpertLLM()
    rag = RAGManager()
    # rag.load_documents_from_directory("data/documents")
    chain = IAChain(ia_llm, rag)
    
    # Generar un ID único para la conversación
    thread_id = str(uuid.uuid4())
    
    print("LLM IA: ¡Hola! Puedes preguntarme cualquier cosa sobre Inteligencia Artificial.")
    print("(Las métricas se registrarán automáticamente en metrics/ia_metrics_report.csv)")
    
    while True:
        question = input("\nUsuario: ")
        if question.lower() in ["salir", "adiós"]:
            print("LLM IA: ¡Hasta luego!")
            break

        response = chain.invoke(
            inputs=question,      # La pregunta del usuario
            thread_id=thread_id,  # ID de la conversación
            use_rag=True          # True = usa RAG, False = solo LLM
        )
        print(f"\nLLM IA: {response}")

if __name__ == "__main__":
    main()
