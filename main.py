from src.Llm import IAExpertLLM

def main():
    ia_llm = IAExpertLLM()
    print("LLM IA: ¡Hola! Puedes preguntarme cualquier cosa sobre Inteligencia Artificial.")
    
    while True:
        question = input("\nUsuario: ")
        if question.lower() in ["salir", "adiós"]:
            print("LLM IA: ¡Hasta luego!")
            break
            
        response = ia_llm.process_question(question)
        print(f"\nLLM IA: {response}")

if __name__ == "__main__":
    main()
