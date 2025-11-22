from src.llm.RAG_manager import RAGManager
from src.llm.Llm import IAExpertLLM
from src.chain.Chain import IAChain
import uuid

def main():
    ia_llm = IAExpertLLM()
    rag = RAGManager()
    chain = IAChain(ia_llm, rag)
    # rag.storage_manager.load_documents_from_directory(directory_path="data/documents",)
    
    thread_id = str(uuid.uuid4())
    
    print("LLM IA: ¡Hola! Puedes preguntarme cualquier cosa sobre Inteligencia Artificial.")
    print("(Las métricas se registrarán automáticamente en metrics/ia_metrics_report.csv)")
    
    while True:
        question = input("\nUsuario: ")
        if question.lower() in ["salir", "adiós"]:
            print("LLM IA: ¡Hasta luego!")
            break

        response = chain.invoke(
            inputs=question,      
            thread_id=thread_id,  
            use_rag=False,
            return_metadata=False,
            mode="extended"
        )
        print(f"\nLLM IA: {response}")

if __name__ == "__main__":
    main()
