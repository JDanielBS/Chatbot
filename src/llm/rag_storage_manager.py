import os
from typing import List
from collections import defaultdict
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
                    loader_cls=TextLoader,
                    loader_kwargs={"autodetect_encoding": True}
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
    def update_chunk_settings(self, chunk_size: int, chunk_overlap: int):
        """Actualiza parámetros de chunking (afecta futuras ingestas)."""
        self.rag.chunk_size = chunk_size
        self.rag.chunk_overlap = chunk_overlap
        print(f"⚙️ Nueva configuración: chunk_size={self.rag.chunk_size}, chunk_overlap={self.rag.chunk_overlap}")
    
    def soft_clear(self):
        """Reinicia la colección Chroma (soft clear)."""
        if self.rag.vector_store:
            self.rag.vector_store.reset_collection()
            print("✅ Colección Chroma reiniciada (soft clear).")
        else:
            print("⚠️ No hay vector_store inicializado.")

    # --------------------------- CONSULTA / LISTADO --------------------------- #
    def list_documents(self) -> List[dict]:
        """Lista documentos indexados agregando por archivo fuente.

        Devuelve una lista con información por archivo:
        - filename: nombre del archivo original
        - chunks: número de fragmentos indexados para ese archivo
        - total_chars: suma de caracteres de esos fragmentos (aprox.)
        - avg_chunk_size: tamaño promedio de chunk (caracteres)

        Returns:
            List[dict]: Información agregada por documento.
        """
        try:
            if self.rag.vector_store is None:
                return []

            collection = self.rag.vector_store._collection
            data = collection.get(include=["metadatas"])  # obtiene todas las metadatas
            metadatas = data.get("metadatas") or []

            agg = defaultdict(lambda: {"chunks": 0, "total_chars": 0})
            for meta in metadatas:
                if not isinstance(meta, dict):
                    continue
                filename = meta.get("original_filename") or meta.get("source") or "Desconocido"
                try:
                    filename = os.path.basename(filename)
                except Exception:
                    pass

                agg[filename]["chunks"] += 1
                try:
                    agg[filename]["total_chars"] += int(meta.get("chunk_size", 0) or 0)
                except Exception:
                    pass

            docs = []
            for name, vals in agg.items():
                chunks = vals["chunks"]
                total_chars = vals["total_chars"]
                avg = int(total_chars / chunks) if chunks else 0
                docs.append({
                    "filename": name,
                    "chunks": chunks,
                    "total_chars": total_chars,
                    "avg_chunk_size": avg,
                })

            docs.sort(key=lambda x: x["filename"])  # orden alfabético
            return docs
        except Exception as e:
            print(f"Error listando documentos: {e}")
            return []

    