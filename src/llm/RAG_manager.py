import os
from typing import List, Tuple
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


from .rag_storage_manager import RAGStorageManager  # Nuevo módulo para operaciones de modificación


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
        chunk_size: int = 800,      # en vez de 1500
        chunk_overlap: int = 150    # en vez de 300
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
            model_name="/models/multilingual-e5-large",
            model_kwargs={'device': 'cpu'},  # En vez de 'cpu'
            encode_kwargs={'normalize_embeddings': True}  # Mejora la similitud coseno
        )
        # Crear la base vectorial directamente (solo lectura en este gestor)
        self.vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
        # Administrador de operaciones de escritura / mantenimiento
        self.storage_manager = RAGStorageManager(self)

    def retrieve_documents(
        self,
        query: str,
        k: int = 5,
        fetch_k: int = 20,
        similarity_margin: float = 0.15,
        min_similarity: float = 0.25,
        max_results: int = 15,
        include_scores: bool = True,
    ) -> List[Tuple[Document, float]]:
        """Recupera documentos relevantes usando una selección por similitud coseno simple.

        Estrategia:
        - Obtener hasta `fetch_k` candidatos desde la base vectorial.
        - Calcular similitud coseno entre query y cada candidato.
        - Seleccionar todos los candidatos cuya similitud >= max(min_similarity, max_sim - similarity_margin).
        - Ordenar por similitud descendente y devolver hasta `max_results`.

        Args:
            query (str): Consulta del usuario.
            k (int): (mantener compatibilidad) número orientativo para consumidores; no limita la selección primaria.
            fetch_k (int): Número de candidatos iniciales a solicitar a la BD.
            similarity_margin (float): Margen respecto a la mejor similitud para incluir más fuentes.
            min_similarity (float): Similitud mínima absoluta para considerar un candidato relevante.
            max_results (int): Máximo de resultados a retornar.
            include_scores (bool): Si True, retorna tuplas (Document, similarity).

        Returns:
            List[Tuple[Document, float]] | List[Document]: Documentos seleccionados (con/sin score).
        """
        if self.is_empty():
            return []
        print(query)

        # Paso 1: pedir candidatos a Chroma (scores devueltos son distancias L2, los ignoramos aquí)
        candidates_with_scores = self.vector_store.similarity_search_with_score(
            query=query,
            k=fetch_k
        )

        if not candidates_with_scores:
            return []

        candidate_docs = [doc for doc, _ in candidates_with_scores]
        candidate_texts = [doc.page_content for doc in candidate_docs]

        # Paso 2: obtener embeddings y normalizarlos para similitud coseno
        query_emb = np.array(self.embeddings.embed_query(query), dtype=np.float32)
        doc_embs = np.array(self.embeddings.embed_documents(candidate_texts), dtype=np.float32)

        # Normalizar (evita división por 0)
        def normalize_rows(arr: np.ndarray) -> np.ndarray:
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            norms[norms == 0] = 1e-8
            return arr / norms

        if doc_embs.ndim == 1:
            doc_embs = doc_embs.reshape(1, -1)

        doc_embs_norm = normalize_rows(doc_embs)
        q_norm = query_emb / (np.linalg.norm(query_emb) + 1e-8)

        # Paso 3: similitudes coseno
        sims = (doc_embs_norm @ q_norm).astype(np.float32)  # valores en [-1,1], mayor = más relevante

        # Paso 4: calcular umbral dinámico cercano al mejor resultado
        max_sim = float(np.max(sims))
        threshold = max(min_similarity, max_sim - similarity_margin)

        # Seleccionar índices que cumplen el umbral
        selected_indices = [i for i, s in enumerate(sims) if s >= threshold]

        if not selected_indices:
            # Si nada pasa el umbral, tomar los top-k por similitud para no devolver vacío
            top_idx = np.argsort(-sims)[:min(k, len(sims))]
            selected_indices = list(top_idx)

        # Ordenar seleccionados por similitud descendente y limitar a max_results
        selected_indices.sort(key=lambda i: sims[i], reverse=True)
        selected_indices = selected_indices[:min(max_results, len(selected_indices))]

        results: List[Tuple[Document, float]] = [
            (candidate_docs[i], float(sims[i])) for i in selected_indices
        ]

        if include_scores:
            return results
        else:
            return [doc for doc, _ in results]

    def build_context(self, query: str, k: int = 5, use_retriever: bool = False) -> Tuple[str, List[Tuple[str, float]]]:
        """Construye contexto formateado y lista de fuentes con scores.

        Args:
            query (str): Consulta del usuario.
            k (int): Número de documentos a incluir (default: 5, optimizado para calidad).
            use_retriever (bool): Si True, usa get_retriever() estándar; si False, usa retrieve_documents() con coseno.

        Returns:
            Tuple[str, List[Tuple[str, float]]]: Contexto concatenado y lista (fuente, score).
        """
        if use_retriever:
            # Método estándar: usa retriever de LangChain (distancia L2, sin re-ranking)
            retriever = self.get_retriever(k=k, search_type="similarity")
            docs = retriever.invoke(query)
            
            if not docs:
                return "No se encontró información relevante en la base de conocimiento.", []
            
            # Como retriever no retorna scores, hacemos búsqueda con score por separado
            docs_with_scores = self.vector_store.similarity_search_with_score(query, k=k)
            retrieved = [(doc, score) for doc, score in docs_with_scores]
        else:
            # Método personalizado: similitud coseno con re-ranking
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
        
        return "\n".join(parts), sources
    
    def get_retriever(self, k: int = 8, search_type: str = "similarity"):
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
    