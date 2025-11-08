from src.RAG_manager import RAGManager
from src.Llm import IAExpertLLM
from src.Chain import IAChain
from langchain_core.messages import HumanMessage
import uuid

def main():
    # Inicializar el LLM y la cadena
    ia_llm = IAExpertLLM()
    rag = RAGManager()
    chain = IAChain(ia_llm, rag)
    # Generar un ID único para la conversación
    thread_id = str(uuid.uuid4())
    
    print("LLM IA: ¡Hola! Puedes preguntarme cualquier cosa sobre Inteligencia Artificial.")
    
    while True:
        question = input("\nUsuario: ")
        if question.lower() in ["salir", "adiós"]:
            print("LLM IA: ¡Hasta luego!")
            break

        response = chain.invoke({"messages": question}, thread_id)
        print(f"\nLLM IA: {response}")

if __name__ == "__main__":
    main()
