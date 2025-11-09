import os
from typing import List, Optional, Tuple
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    DirectoryLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from dotenv import load_dotenv

load_dotenv()


class RAGManager:
    """
    Gestor de RAG (Retrieval-Augmented Generation) para el chatbot de IA.
    
    RESPONSABILIDADES:
    - Cargar y procesar documentos (PDF, TXT, etc.)
    - Gestionar la base de datos vectorial (Chroma)
    - Realizar búsquedas de similitud
    - Proporcionar retrievers configurados para consultas
    - Mantener estadísticas de la base de conocimiento
    
    Attributes:
        embeddings (GoogleGenerativeAIEmbeddin gs): Modelo de embeddings de Google
        vector_store (Chroma): Base de datos vectorial Chroma
        persist_directory (str): Directorio donde se persiste la BD vectorial
        chunk_size (int): Tamaño de los chunks de texto
        chunk_overlap (int): Superposición entre chunks
    """
    
    def __init__(
        self, 
        persist_directory: str = "./data/chroma_db",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Inicializa el gestor de RAG.
        
        Args:
            persist_directory (str): Ruta donde se guardará la base de datos vectorial.
            chunk_size (int): Tamaño de los chunks de texto.
            chunk_overlap (int): Superposición entre chunks consecutivos.
        """
        self.persist_directory = persist_directory
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Inicializar embeddings (modelo multilingüe para mejorar recall cross-lingual)
        # Elegimos un modelo multilingual pequeño que soporta búsqueda entre ES/EN
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        # Cargar o crear la base de datos vectorial
        self.vector_store = None
        self._load_or_create_vectorstore()
    
    def _load_or_create_vectorstore(self):
        """
        Carga la base de datos vectorial si existe, o crea una nueva.
        """
        self.vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
    
    def load_documents_from_directory(
        self, 
        directory_path: str,
        file_types: List[str] = ["pdf", "txt"]
    ) -> int:
        """
        Carga documentos desde un directorio especificado.
        
        Args:
            directory_path (str): Ruta al directorio con documentos
            file_types (List[str]): Tipos de archivo a cargar (pdf, txt, etc.)
        
        Returns:
            int: Número de documentos cargados exitosamente
        
        Raises:
            ValueError: Si el directorio no existe
        """
        if not os.path.exists(directory_path):
            raise ValueError(f"El directorio {directory_path} no existe")
        
        documents = []
        
        # Cargar PDFs
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
        
        # Cargar archivos de texto
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
        else:
            return 0
    
    def load_single_document(self, file_path: str) -> bool:
        """
        Carga un documento individual.
        
        Args:
            file_path (str): Ruta completa al archivo
        
        Returns:
            bool: True si se cargó exitosamente, False en caso contrario
        """
        if not os.path.exists(file_path):
            print(f"El archivo {file_path} no existe")
            return False
        
        try:
            # Determinar el tipo de archivo y usar el loader apropiado
            if file_path.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith('.txt'):
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
    
    def _process_and_store_documents(self, documents: List[Document]):
        """
        Procesa documentos dividiéndolos en chunks y los almacena en la BD vectorial.
        
        Args:
            documents (List[Document]): Lista de documentos a procesar
        """
        # Dividir documentos en chunks más pequeños
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        splits = text_splitter.split_documents(documents)

        # Enriquecer metadata para trazabilidad y auditoría
        total = len(splits)
        for idx, doc in enumerate(splits):
            meta = doc.metadata or {}
            meta["chunk_index"] = idx
            meta["total_chunks"] = total
            meta["chunk_size"] = len(doc.page_content)
            if "source" in meta:
                meta["original_filename"] = os.path.basename(meta["source"])
            meta["embedding_model"] = self.embeddings.model_name
            doc.metadata = meta

        # Insertar documentos enriquecidos
        self.vector_store.add_documents(splits)

    # ========================= NUEVO MÉTODO PRINCIPAL DE RECUPERACIÓN =========================
    def retrieve_documents(
        self,
        query: str,
        k: int = 6,
        fetch_k: int = 20,
        diversity_lambda: float = 0.5,
        score_threshold: Optional[float] = None,
        include_scores: bool = True,
    ) -> List[Tuple[Document, float]]:
        """Recupera documentos relevantes usando MMR para mayor diversidad.

        Prioriza diversidad y relevancia simultáneamente, permitiendo reducir
        alucinaciones y aumentar cobertura de distintas fuentes.

        Args:
            query (str): Consulta del usuario.
            k (int): Número de documentos finales.
            fetch_k (int): Número de candidatos iniciales antes de MMR.
            diversity_lambda (float): Parámetro de diversidad (0 más diversidad, 1 más similitud pura).
            score_threshold (Optional[float]): Filtro de score mínimo (0-1 si vectorstore lo normaliza).
            include_scores (bool): Si True, retorna tuplas (Document, score).

        Returns:
            List[Tuple[Document, float]] | List[Document]: Lista de documentos con o sin score.
        """
        if self.is_empty():
            return []

        # Usamos búsqueda MMR para diversidad; Chroma expone max_marginal_relevance_search
        # NOTA: Esta búsqueda no retorna scores directamente, por lo que realizamos
        # una segunda pasada para obtener scores de similitud de cada documento recuperado.
        mmr_docs = self.vector_store.max_marginal_relevance_search(
            query=query,
            k=k,
            fetch_k=fetch_k,
            lambda_mult=diversity_lambda,
        )

        # Obtener scores para cada documento (similarity_search_with_score)
        # Realizamos embedding de la query una sola vez (ya optimizado internamente por Chroma)
        scored = self.vector_store.similarity_search_with_score(query, k=fetch_k)
        # Crear índice por contenido para asociar score (simplificación; en producción usar IDs)
        score_map = {}
        for doc, score in scored:
            score_map.setdefault(doc.page_content, score)

        result: List[Tuple[Document, float]] = []
        for d in mmr_docs:
            sc = score_map.get(d.page_content, 0.0)
            result.append((d, sc))

        # Aplicar threshold si se solicita
        if score_threshold is not None:
            result = [pair for pair in result if pair[1] >= score_threshold]

        # Ordenar por score descendente para priorizar mejor evidencia
        result.sort(key=lambda x: x[1], reverse=True)

        if include_scores:
            return result[:k]
        else:
            return [doc for doc, _ in result[:k]]

    def build_context(self, query: str, k: int = 6) -> Tuple[str, List[Tuple[str, float]]]:
        """Construye contexto formateado y lista de fuentes con scores.

        Args:
            query (str): Consulta del usuario.
            k (int): Número de documentos a incluir.

        Returns:
            Tuple[str, List[Tuple[str, float]]]: Contexto concatenado y lista (fuente, score).
        """
        retrieved = self.retrieve_documents(query=query, k=k, include_scores=True)
        if not retrieved:
            return "No se encontró información relevante en la base de conocimiento.", []

        parts = []
        sources: List[Tuple[str, float]] = []
        for i, (doc, score) in enumerate(retrieved, 1):
            source = doc.metadata.get("original_filename") or doc.metadata.get("source", "Desconocido")
            parts.append(f"[Fuente {i}: {source} | score={score:.4f} | chunk={doc.metadata.get('chunk_index')}/{doc.metadata.get('total_chunks')}]\n{doc.page_content}\n")
            sources.append((source, score))
        return "\n".join(parts), sources
    
    def get_retriever(self, k: int = 4, search_type: str = "similarity"):
        """
        Obtiene un retriever configurado para usar con cadenas de LangChain.
        
        Args:
            k (int): Número de documentos a recuperar
            search_type (str): Tipo de búsqueda ("similarity", "mmr", "similarity_score_threshold")
        
        Returns:
            VectorStoreRetriever: Retriever configurado
        """
        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs={"k": k}
        )
    
    def get_relevant_context(self, query: str, k: int = 6) -> str:
        """Devuelve el contexto enriquecido usando MMR y metadatos de trazabilidad."""
        context, _ = self.build_context(query=query, k=k)
        return context
    
    def clear_database(self):
        """
        Elimina todos los documentos de la base de datos vectorial.
        
        ADVERTENCIA: Esta operación es irreversible.
        """
        import shutil
        if os.path.exists(self.persist_directory):
            shutil.rmtree(self.persist_directory)
            print(f"🗑️ Base de datos vectorial eliminada de {self.persist_directory}")
            self._load_or_create_vectorstore()
        else:
            print("⚠️ No hay base de datos para eliminar")
    
    def get_stats(self) -> dict:
        """
        Obtiene estadísticas de la base de datos vectorial.
        
        Returns:
            dict: Diccionario con estadísticas (número de documentos, etc.)
        """
        try:
            collection = self.vector_store._collection
            count = collection.count()
            return {
                "total_chunks": count,
                "persist_directory": self.persist_directory,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "status": "✅ Operacional"
            }
        except Exception as e:
            return {
                "error": str(e),
                "persist_directory": self.persist_directory,
                "status": "❌ Error"
            }
    
    def is_empty(self) -> bool:
        """
        Verifica si la base de datos vectorial está vacía.
        
        Returns:
            bool: True si está vacía, False si tiene documentos
        """
        try:
            stats = self.get_stats()
            return stats.get("total_chunks", 0) == 0
        except:
            return True
    
    def update_chunk_settings(self, chunk_size: int, chunk_overlap: int):
        """
        Actualiza la configuración de chunks.
        
        Nota: Solo afecta a documentos cargados DESPUÉS de este cambio.
        
        Args:
            chunk_size (int): Nuevo tamaño de chunks
            chunk_overlap (int): Nueva superposición entre chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        print(f"⚙️ Configuración actualizada: chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")