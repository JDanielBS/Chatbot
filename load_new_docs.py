"""Script simple para cargar documentos desde data/new-docs"""

from src.llm.RAG_manager import RAGManager

# Inicializar
rag = RAGManager()

rag.storage_manager.soft_clear()

# Cargar nuevos documentos
print("Cargando documentos desde data/new-docs...")
num = rag.storage_manager.load_documents_from_directory(
    "./data/new-docs",
    file_types=["txt"]
)

print(f"✅ {num} documentos cargados")
print(f"Total chunks: {rag.get_stats()['total_chunks']}")


