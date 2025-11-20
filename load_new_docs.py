"""Script simple para cargar documentos desde data/new-docs"""

from src.llm.RAG_manager import RAGManager

# Inicializar
rag = RAGManager()

# Opción: Eliminar base existente antes de cargar nuevos documentos
# Si quieres AGREGAR documentos a los existentes, comenta las siguientes 2 líneas
# Si quieres REEMPLAZAR toda la base, déjalas activas
CLEAR_BEFORE_LOAD = false  # Cambia a False para agregar sin eliminar

if CLEAR_BEFORE_LOAD:
    print("Eliminando base anterior...")
    rag.storage_manager.clear_database()

# Cargar nuevos documentos
print("Cargando documentos desde data/new-docs...")
num = rag.storage_manager.load_documents_from_directory(
    "./data/new-docs",
    file_types=["txt"]
)

print(f"✅ {num} documentos cargados")
print(f"Total chunks: {rag.get_stats()['total_chunks']}")


