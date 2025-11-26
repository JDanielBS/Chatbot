"""
Endpoints para gestión de documentos.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, status, BackgroundTasks
from pydantic import BaseModel

from api.dependencies import get_rag_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

# Carpeta donde se guardan los documentos
DOCS_FOLDER = Path("data/new-docs")
DOCS_FOLDER.mkdir(parents=True, exist_ok=True)

# Extensiones permitidas
ALLOWED_EXTENSIONS = {".txt", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024

# Estado global de la recarga
reload_status = {
    "in_progress": False,
    "last_result": None,
    "last_error": None,
    "started_at": None,
    "finished_at": None,
    "docs_count": 0
}


class DocumentInfo(BaseModel):
    filename: str
    size: int
    uploaded_at: str
    extension: str


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total: int


class UploadResponse(BaseModel):
    success: bool
    filename: str
    message: str


@router.get(
    "/list",
    response_model=DocumentListResponse,
    summary="Listar documentos disponibles"
)
async def list_documents():
    """Lista todos los documentos en la carpeta new-docs."""
    documents = []
    
    if DOCS_FOLDER.exists():
        for file_path in DOCS_FOLDER.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ALLOWED_EXTENSIONS:
                stat = file_path.stat()
                documents.append(DocumentInfo(
                    filename=file_path.name,
                    size=stat.st_size,
                    uploaded_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    extension=file_path.suffix.lower()
                ))
    
    # Ordenar por fecha de subida (más recientes primero)
    documents.sort(key=lambda x: x.uploaded_at, reverse=True)
    
    return DocumentListResponse(
        documents=documents,
        total=len(documents)
    )


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Subir un documento"
)
async def upload_document(file: UploadFile = File(...)):
    """
    Sube un documento .txt o .pdf a la carpeta new-docs.
    """
    # Validar extensión
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido. Solo: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Leer contenido para validar tamaño
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Archivo muy grande. Máximo: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Sanitizar nombre del archivo
    safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._- ")
    if not safe_filename:
        safe_filename = f"documento_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
    
    # Evitar sobrescribir archivos existentes
    file_path = DOCS_FOLDER / safe_filename
    if file_path.exists():
        base_name = file_path.stem
        counter = 1
        while file_path.exists():
            file_path = DOCS_FOLDER / f"{base_name}_{counter}{file_ext}"
            counter += 1
        safe_filename = file_path.name
    
    # Guardar archivo
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
        
        return UploadResponse(
            success=True,
            filename=safe_filename,
            message=f"Documento '{safe_filename}' subido correctamente"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar archivo: {str(e)}"
        )


@router.delete(
    "/{filename}",
    summary="Eliminar un documento"
)
async def delete_document(filename: str):
    """Elimina un documento de la carpeta new-docs."""
    file_path = DOCS_FOLDER / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    
    # Verificar que está dentro de la carpeta permitida
    if not file_path.resolve().is_relative_to(DOCS_FOLDER.resolve()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ruta de archivo inválida"
        )
    
    try:
        file_path.unlink()
        return {"success": True, "message": f"Documento '{filename}' eliminado"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar: {str(e)}"
        )


def _reload_documents_task():
    """Tarea en background para recargar documentos."""
    global reload_status
    try:
        logger.info("📚 [BACKGROUND] Iniciando recarga de documentos...")
        
        rag = get_rag_manager()
        
        logger.info("🗑️ [BACKGROUND] Limpiando base vectorial...")
        rag.storage_manager.soft_clear()
        
        logger.info(f"📂 [BACKGROUND] Cargando documentos desde {DOCS_FOLDER}...")
        result = rag.storage_manager.load_documents_from_directory(str(DOCS_FOLDER))
        
        reload_status["last_result"] = result
        reload_status["last_error"] = None
        reload_status["finished_at"] = datetime.now().isoformat()
        
        logger.info(f"✅ [BACKGROUND] Recarga completada: {result}")
        
    except Exception as e:
        logger.error(f"❌ [BACKGROUND] Error en recarga: {str(e)}")
        reload_status["last_error"] = str(e)
        reload_status["last_result"] = None
        reload_status["finished_at"] = datetime.now().isoformat()
    finally:
        reload_status["in_progress"] = False


@router.post(
    "/reload",
    summary="Recargar documentos en el RAG"
)
async def reload_documents(background_tasks: BackgroundTasks):
    """
    Inicia la recarga de documentos en segundo plano.
    
    Responde inmediatamente y procesa en background para evitar timeouts.
    """
    global reload_status
    
    # Verificar si ya hay una recarga en progreso
    if reload_status["in_progress"]:
        return {
            "success": False,
            "message": "Ya hay una recarga en progreso. Espera a que termine.",
            "status": "in_progress",
            "started_at": reload_status["started_at"]
        }
    
    # Verificar que hay documentos
    docs_count = len([f for f in DOCS_FOLDER.iterdir() if f.is_file()])
    if docs_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay documentos en la carpeta new-docs"
        )
    
    # Iniciar tarea en background
    reload_status["in_progress"] = True
    reload_status["started_at"] = datetime.now().isoformat()
    reload_status["finished_at"] = None
    reload_status["last_result"] = None
    reload_status["last_error"] = None
    reload_status["docs_count"] = docs_count
    
    background_tasks.add_task(_reload_documents_task)
    
    logger.info(f"🚀 Recarga iniciada en background para {docs_count} documentos")
    
    return {
        "success": True,
        "message": f"Recarga iniciada para {docs_count} documentos. Procesando en segundo plano...",
        "status": "started",
        "docs_count": docs_count
    }


@router.get(
    "/reload/status",
    summary="Estado de la recarga de documentos"
)
async def get_reload_status():
    """
    Consulta el estado de la última recarga de documentos.
    
    Útil para saber si la recarga en background terminó.
    """
    return {
        "in_progress": reload_status["in_progress"],
        "started_at": reload_status["started_at"],
        "finished_at": reload_status["finished_at"],
        "docs_count": reload_status["docs_count"],
        "last_result": reload_status["last_result"],
        "last_error": reload_status["last_error"]
    }

