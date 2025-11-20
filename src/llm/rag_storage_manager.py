import os
from typing import List
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    DirectoryLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_chroma import Chroma


class RAGStorageManager:
    """Gestiona operaciones de modificación sobre la base vectorial Chroma.

    Esta clase separa responsabilidades: únicamente crea, carga, elimina y
    reconfigura cómo se indexan los documentos. No implementa funciones de
    recuperación avanzada (RAG), que permanecen en `RAGManager`.

    Args:
        rag_manager: Instancia de `RAGManager` para acceder a embeddings,
                     configuración de chunks y vector_store.
    """

    def __init__(self, rag_manager):
        self.rag = rag_manager

    # ----------------------------- CARGA MASIVA ----------------------------- #
    def load_documents_from_directory(
        self,
        directory_path: str,
        file_types: List[str] = ["pdf", "txt"]
    ) -> int:
        """Carga e indexa todos los documentos soportados de un directorio.

        Retorna el número total de documentos (archivos) cargados. Los
        documentos se dividen en chunks y se añaden a la base vectorial.
        """
        if not os.path.exists(directory_path):
            raise ValueError(f"El directorio {directory_path} no existe")

        documents = []

        if "pdf" in file_types:
            try:
                pdf_loader = DirectoryLoader(
                    directory_path,
                    glob="**/*.pdf",
                    loader_cls=PyPDFLoader,
                    show_progress=True
                )
                pdf_docs = pdf_loader.load()
                documents.extend(pdf_docs)
                print(f"Cargados {len(pdf_docs)} archivos PDF")
            except Exception as e:
                print(f"Error cargando PDFs: {e}")

        if "txt" in file_types:
            try:
                txt_loader = DirectoryLoader(
                    directory_path,
                    glob="**/*.txt",
                    loader_cls=TextLoader
                )
                txt_docs = txt_loader.load()
                documents.extend(txt_docs)
                print(f"Cargados {len(txt_docs)} archivos TXT")
            except Exception as e:
                print(f"Error cargando TXTs: {e}")

        if documents:
            self._process_and_store_documents(documents)
            return len(documents)
        return 0

    # ----------------------------- CARGA SIMPLE ---------------------------- #
    def load_single_document(self, file_path: str) -> bool:
        """Carga e indexa un único documento PDF o TXT."""
        if not os.path.exists(file_path):
            print(f"El archivo {file_path} no existe")
            return False

        try:
            if file_path.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith(".txt"):
                loader = TextLoader(file_path)
            else:
                print(f"Tipo de archivo no soportado: {file_path}")
                return False

            documents = loader.load()
            self._process_and_store_documents(documents)
            print(f"Documento cargado exitosamente: {file_path}")
            return True
        except Exception as e:
            print(f"Error al cargar {file_path}: {e}")
            return False

    # --------------------- PROCESAMIENTO / INDEXACIÓN ---------------------- #
    def _process_and_store_documents(self, documents: List[Document]):
        """Divide documentos en chunks y los inserta con metadata enriquecida."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.rag.chunk_size,
            chunk_overlap=self.rag.chunk_overlap,
            length_function=len,
            separators=["\n\n\n", "\n\n", "\n", ". ", " ", ""],
            keep_separator=True
        )

        print(f"Dividiendo documentos en chunks (esto puede tardar)...")
        splits = splitter.split_documents(documents)
        print(f"✓ Creados {len(splits)} chunks")
        print(f"Calculando embeddings y almacenando (puede tardar varios minutos)...")

        batch_size = 100
        for i in range(0, len(splits), batch_size):
            batch = splits[i:i + batch_size]
            self.rag.vector_store.add_documents(batch)
            print(f"Procesados {min(i + batch_size, len(splits))}/{len(splits)} chunks")

    # --------------------------- MANTENIMIENTO ----------------------------- #
    def clear_database(self):
        """Elimina todos los datos persistidos y recrea la colección como si fuera la primera vez."""
        # Eliminar la colección usando la API de ChromaDB (evita problemas de locks en Windows)
        try:
            if hasattr(self.rag.vector_store, '_collection'):
                collection_name = self.rag.vector_store._collection.name
                if hasattr(self.rag.vector_store, '_client'):
                    client = self.rag.vector_store._client
                    try:
                        # Eliminar la colección usando la API de ChromaDB
                        client.delete_collection(name=collection_name)
                        print(f"🗑️ Colección '{collection_name}' eliminada")
                    except Exception as api_error:
                        print(f"⚠️ No se pudo eliminar colección por API: {api_error}")
        except Exception as e:
            print(f"⚠️ Advertencia al eliminar colección: {e}")
        
        # Cerrar el vector_store actual para liberar recursos
        try:
            del self.rag.vector_store
        except:
            pass
        
        # Recrear vector store limpio (ChromaDB creará una nueva colección automáticamente)
        # Esto es como si fuera la primera vez que se usa
        self.rag.vector_store = Chroma(
            persist_directory=self.rag.persist_directory,
            embedding_function=self.rag.embeddings
        )
        print("✅ Base vectorial reinicializada (lista para nuevos documentos)")

    def update_chunk_settings(self, chunk_size: int, chunk_overlap: int):
        """Actualiza parámetros de chunking (afecta futuras ingestas)."""
        self.rag.chunk_size = chunk_size
        self.rag.chunk_overlap = chunk_overlap
        print(f"⚙️ Nueva configuración: chunk_size={self.rag.chunk_size}, chunk_overlap={self.rag.chunk_overlap}")