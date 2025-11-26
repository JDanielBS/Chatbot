"""
Endpoints para gestión de documentos.
"""

from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel

from api.dependencies import get_rag_manager

router = APIRouter(prefix="/documents", tags=["Documents"])

# Carpeta donde se guardan los documentos
DOCS_FOLDER = Path("data/new-docs")
DOCS_FOLDER.mkdir(parents=True, exist_ok=True)

# Extensiones permitidas
ALLOWED_EXTENSIONS = {".txt", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  


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


@router.post(
    "/reload",
    summary="Recargar documentos en el RAG"
)
async def reload_documents():
    """
    Recarga todos los documentos de new-docs en la base vectorial.
    
    Esto limpia la base vectorial y la reconstruye.
    """
    try:
        rag = get_rag_manager()
        
        # Verificar que hay documentos
        docs_count = len([f for f in DOCS_FOLDER.iterdir() if f.is_file()])
        if docs_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay documentos en la carpeta new-docs"
            )
        
        # Recargar documentos
        rag.storage_manager.soft_clear()
        result = rag.storage_manager.load_documents_from_directory(str(DOCS_FOLDER))
        
        return {
            "success": True,
            "message": "Documentos recargados correctamente",
            "details": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al recargar: {str(e)}"
        )

