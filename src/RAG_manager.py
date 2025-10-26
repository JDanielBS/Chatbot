import os
from typing import List, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
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
        embeddings (GoogleGenerativeAIEmbeddings): Modelo de embeddings de Google
        vector_store (Chroma): Base de datos vectorial Chroma
        persist_directory (str): Directorio donde se persiste la BD vectorial
        chunk_size (int): Tamaño de los chunks de texto
        chunk_overlap (int): Superposición entre chunks
    """
    
    def __init__(
        self, 
        persist_directory: str = "./chroma_db",
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
        
        # Inicializar embeddings de Google
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        
        # Cargar o crear la base de datos vectorial
        self.vector_store = None
        self._load_or_create_vectorstore()
    
    def _load_or_create_vectorstore(self):
        """
        Carga la base de datos vectorial si existe, o crea una nueva.
        """
        if os.path.exists(self.persist_directory):
            print(f"📂 Cargando base de datos vectorial desde {self.persist_directory}")
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        else:
            print(f"🆕 Creando nueva base de datos vectorial en {self.persist_directory}")
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
            raise ValueError(f"❌ El directorio {directory_path} no existe")
        
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
                print(f"📄 Cargados {len(pdf_docs)} archivos PDF")
            except Exception as e:
                print(f"⚠️ Error cargando PDFs: {e}")
        
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
                print(f"📝 Cargados {len(txt_docs)} archivos TXT")
            except Exception as e:
                print(f"⚠️ Error cargando TXTs: {e}")
        
        if documents:
            self._process_and_store_documents(documents)
            print(f"✅ Total: {len(documents)} documentos cargados desde {directory_path}")
            return len(documents)
        else:
            print("⚠️ No se encontraron documentos para cargar")
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
            print(f"❌ El archivo {file_path} no existe")
            return False
        
        try:
            # Determinar el tipo de archivo y usar el loader apropiado
            if file_path.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith('.txt'):
                loader = TextLoader(file_path)
            else:
                print(f"❌ Tipo de archivo no soportado: {file_path}")
                return False
            
            documents = loader.load()
            self._process_and_store_documents(documents)
            print(f"✅ Documento cargado exitosamente: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error al cargar {file_path}: {e}")
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
        
        # Agregar a la base de datos vectorial
        self.vector_store.add_documents(splits)
        
        # Persistir los cambios
        self.vector_store.persist()
        
        print(f"💾 Procesados y almacenados {len(splits)} chunks")
    
    def search_similar_documents(
        self, 
        query: str, 
        k: int = 4,
        score_threshold: Optional[float] = None
    ) -> List[Document]:
        """
        Busca documentos similares a la consulta.
        
        Args:
            query (str): Consulta de búsqueda
            k (int): Número de documentos a retornar (por defecto 4)
            score_threshold (float, optional): Umbral mínimo de similitud
        
        Returns:
            List[Document]: Lista de documentos relevantes encontrados
        """
        if score_threshold is not None:
            # Búsqueda con threshold de similitud
            results = self.vector_store.similarity_search_with_score(query, k=k)
            filtered_results = [
                doc for doc, score in results if score >= score_threshold
            ]
            return filtered_results
        else:
            # Búsqueda simple
            return self.vector_store.similarity_search(query, k=k)
    
    def search_with_scores(
        self,
        query: str,
        k: int = 4
    ) -> List[tuple[Document, float]]:
        """
        Busca documentos similares y retorna con sus scores de similitud.
        
        Args:
            query (str): Consulta de búsqueda
            k (int): Número de documentos a retornar
        
        Returns:
            List[tuple[Document, float]]: Lista de tuplas (documento, score)
        """
        return self.vector_store.similarity_search_with_score(query, k=k)
    
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
    
    def get_relevant_context(self, query: str, k: int = 4) -> str:
        """
        Obtiene el contexto relevante como una cadena de texto formateada.
        
        Args:
            query (str): Consulta para buscar contexto
            k (int): Número de documentos a recuperar
        
        Returns:
            str: Contexto formateado listo para incluir en un prompt
        """
        docs = self.search_similar_documents(query, k=k)
        
        if not docs:
            return "No se encontró información relevante en la base de conocimiento."
        
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('source', 'Desconocido')
            context_parts.append(f"[Fuente {i}: {source}]\n{doc.page_content}\n")
        
        return "\n".join(context_parts)
    
    def clear_database(self):
        """
        Elimina todos los documentos de la base de datos vectorial.
        
        ⚠️ ADVERTENCIA: Esta operación es irreversible.
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