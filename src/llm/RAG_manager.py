import os
from typing import List, Optional, Tuple
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_chroma.vectorstores import maximal_marginal_relevance
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    DirectoryLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from dotenv import load_dotenv

import numpy as np

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
        chunk_size: int = 1500,
        chunk_overlap: int = 300
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
        
        # Inicializar embeddings con modelo más potente para mejor semántica
        # all-MiniLM-L6-v2 tiene mejor rendimiento en búsqueda semántica general
        # y es más rápido que el modelo anterior manteniendo buena calidad
        self.embeddings = HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-large",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}  # Mejora la similitud coseno
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
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n\n", "\n\n", "\n", ". ", " ", ""],
            keep_separator=True
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

        self.vector_store.add_documents(splits)

    def retrieve_documents(
        self,
        query: str,
        k: int = 5,
        fetch_k: int = 15,
        diversity_lambda: float = 0.6,
        score_threshold: Optional[float] = None,
        include_scores: bool = True,
    ) -> List[Tuple[Document, float]]:
        """Recupera documentos relevantes usando búsqueda híbrida optimizada.

        Estrategia mejorada:
        1. Primero obtiene candidatos con scores (fetch_k documentos)
        2. Filtra por score_threshold si se especifica
        3. Aplica MMR solo a los mejores candidatos para balance relevancia/diversidad
        4. Retorna los k mejores documentos con sus scores reales

        Args:
            query (str): Consulta del usuario.
            k (int): Número de documentos finales (default: 5, reducido para mejor calidad).
            fetch_k (int): Número de candidatos iniciales (default: 15, optimizado).
            diversity_lambda (float): Balance diversidad/relevancia (0.6 = 60% relevancia, 40% diversidad).
            score_threshold (Optional[float]): Filtro de score mínimo. None = sin filtro.
            include_scores (bool): Si True, retorna tuplas (Document, score).

        Returns:
            List[Tuple[Document, float]] | List[Document]: Lista de documentos con o sin score.
        """
        if self.is_empty():
            return []

        # PASO 1: Obtener candidatos iniciales CON SCORES
        candidates_with_scores = self.vector_store.similarity_search_with_score(
            query=query, 
            k=fetch_k
        )
        
        # PASO 2: Filtrar por threshold si se especifica (Chroma usa distancia L2, menor = mejor)
        if score_threshold is not None:
            # Nota: Chroma retorna distancias, no similitudes. 
            # Distancia menor = más similar. Threshold debería ser distancia máxima aceptable.
            candidates_with_scores = [
                (doc, score) for doc, score in candidates_with_scores 
                if score <= score_threshold  # Invertido: menor distancia es mejor
            ]
        
        if not candidates_with_scores:
            return []
        
        # PASO 3: Extraer embeddings de candidatos para aplicar MMR manualmente
        # Obtenemos el embedding de la query
        query_embedding = self.embeddings.embed_query(query)
        
        # Extraer documentos candidatos
        candidate_docs = [doc for doc, _ in candidates_with_scores]
        
        # Obtener embeddings de los documentos candidatos
        candidate_texts = [doc.page_content for doc in candidate_docs]
        candidate_embeddings = self.embeddings.embed_documents(candidate_texts)
        
        # PASO 4: Aplicar MMR usando la función de Chroma
        mmr_indices = maximal_marginal_relevance(
            query_embedding=np.array(query_embedding, dtype=np.float32),
            embedding_list=candidate_embeddings,
            lambda_mult=diversity_lambda,
            k=min(k, len(candidate_docs))
        )
        
        # PASO 5: Construir resultado final con documentos seleccionados y sus scores originales
        result: List[Tuple[Document, float]] = []
        for idx in mmr_indices:
            doc = candidate_docs[idx]
            # Buscar el score original
            original_score = next(
                score for d, score in candidates_with_scores 
                if d.page_content == doc.page_content
            )
            result.append((doc, original_score))
        
        if include_scores:
            return result
        else:
            return [doc for doc, _ in result]

    def build_context(self, query: str, k: int = 5) -> Tuple[str, List[Tuple[str, float]]]:
        """Construye contexto formateado y lista de fuentes con scores.

        Args:
            query (str): Consulta del usuario.
            k (int): Número de documentos a incluir (default: 5, optimizado para calidad).

        Returns:
            Tuple[str, List[Tuple[str, float]]]: Contexto concatenado y lista (fuente, score).
        """
        retrieved = self.retrieve_documents(query=query, k=k, include_scores=True)
        if not retrieved:
            return "No se encontró información relevante en la base de conocimiento.", []

        parts = []
        sources: List[Tuple[str, float]] = []
        seen_sources = set()  # Para evitar duplicados de la misma fuente
        
        for i, (doc, score) in enumerate(retrieved, 1):
            source = doc.metadata.get("original_filename") or doc.metadata.get("source", "Desconocido")
            
            # Marcar fuente como vista
            if source not in seen_sources:
                seen_sources.add(source)
            
            # Formatear con información de relevancia
            relevance = "Alta" if score < 0.5 else "Media" if score < 1.0 else "Baja"
            parts.append(
                f"[Fuente {i}: {source} | Relevancia: {relevance} (distancia={score:.4f})]\n"
                f"{doc.page_content}\n"
            )
            sources.append((source, score))
        
        # Agregar resumen de diversidad de fuentes
        diversity_info = f"\n[INFO: Se consultaron {len(seen_sources)} fuentes distintas de {len(retrieved)} fragmentos]\n"
        
        return "\n".join(parts) + diversity_info, sources
    
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
    
    def get_relevant_context(self, query: str, k: int = 5) -> str:
        """Devuelve el contexto enriquecido usando búsqueda híbrida optimizada.
        
        Args:
            query (str): Consulta del usuario.
            k (int): Número de documentos a incluir (default: 5, optimizado).
        
        Returns:
            str: Contexto formateado con información de fuentes y relevancia.
        """
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
                "status": "operacional"
            }
        except Exception as e:
            return {
                "error": str(e),
                "persist_directory": self.persist_directory,
                "status": "error"
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