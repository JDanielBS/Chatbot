"""
Aplicación principal FastAPI para el Chatbot de IA con RAG.

Este es el punto de entrada de la API REST que proporciona endpoints
para interactuar con el chatbot especializado en Inteligencia Artificial.

Características:
- Chat conversacional con RAG
- Citación automática de fuentes
- Métricas de rendimiento
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time

from api.models import ErrorResponse
from api.routes import chat, system, whatsapp, telegram, metrics, auth, documents
from api.dependencies import (
    get_settings,
    get_rag_manager,
    get_llm_gemini,
    get_chain,
    get_timestamp
)
from api.database.config import create_db_and_tables
from api.services.auth_service import create_default_admin


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación.
    
    - Startup: Inicializa componentes necesarios
    - Shutdown: Limpia recursos
    """
    # STARTUP
    print("\n" + "="*70)
    print("INICIANDO API DEL CHATBOT DE IA")
    print("="*70)
    
    try:
        # Inicializar base de datos
        print("\n📦 Inicializando base de datos...")
        create_db_and_tables()
        print("   ✅ Base de datos SQLite lista")
        
        # Crear admin por defecto
        from sqlmodel import Session
        from api.database.config import engine
        with Session(engine) as session:
            create_default_admin(session)
        
        # Crear archivo de métricas si no existe
        import os
        import csv
        metrics_dir = "./metrics"
        metrics_file = os.path.join(metrics_dir, "ia_metrics_report.csv")
        
        if not os.path.exists(metrics_dir):
            os.makedirs(metrics_dir)
            print("   📊 Carpeta de métricas creada")
        
        if not os.path.exists(metrics_file):
            # Headers del CSV de métricas
            headers = [
                "timestamp", "thread_id", "platform", "query", "response",
                "latency_ms", "input_tokens", "output_tokens", "total_tokens",
                "estimated_cost_usd", "model", "num_retrieved_docs", "context_size",
                "avg_similarity_score", "citations_total", "citations_valid",
                "citation_validity_ratio", "hallucination_rate"
            ]
            with open(metrics_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            print("   📊 Archivo de métricas inicializado")
        
        # Inicializar componentes singleton
        print("\nInicializando componentes...")
        
        # RAG Manager
        rag = get_rag_manager()
        stats = rag.get_stats()
        chunks_count = stats.get('total_chunks', 0)
        print(f"   RAG Manager: {chunks_count} chunks cargados")
        
        # Auto-cargar documentos si la base está vacía
        if chunks_count == 0:
            print("\n📚 Base vectorial vacía. Cargando documentos automáticamente...")
            docs_dir = "./data/new-docs"
            import os
            if os.path.exists(docs_dir):
                try:
                    num_docs = rag.storage_manager.load_documents_from_directory(
                        directory_path=docs_dir,
                        file_types=["txt", "pdf"]
                    )
                    print(f"✅ Cargados {num_docs} documentos automáticamente")
                    # Actualizar stats
                    stats = rag.get_stats()
                    print(f"   RAG Manager: {stats.get('total_chunks', 0)} chunks ahora")
                except Exception as e:
                    print(f"⚠️ Error cargando documentos: {e}")
            else:
                print(f"⚠️ Directorio {docs_dir} no encontrado")
        
        print("\n" + "="*70)
        print("API LISTA PARA RECIBIR PETICIONES")
        print("="*70)
        print(f"Documentación: http://localhost:8000/docs")
        print(f"Estado: http://localhost:8000/api/health")
        print(f"Estadísticas: http://localhost:8000/api/stats")
        print(f"Chat: http://localhost:8000/api/chat")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\nERROR AL INICIALIZAR: {e}")
        print("La API iniciará pero puede tener problemas\n")
    
    yield  
    
    print("\n" + "="*70)
    print("CERRANDO API DEL CHATBOT DE IA")
    print("="*70)



# ============================================================================
# CREAR APLICACIÓN
# ============================================================================

settings = get_settings()

app = FastAPI(
    title=settings["app_name"],
    description=settings["description"],
    version=settings["version"],
    docs_url=settings["docs_url"],
    redoc_url=settings["redoc_url"],
    lifespan=lifespan,
    contact={
        "name": "Universidad de Caldas",
        "url": "https://www.ucaldas.edu.co"
    },
    license_info={
        "name": "MIT",
    }
)


# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS - Permitir peticiones desde frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware para loggear todas las peticiones.
    """
    start_time = time.time()

    print(f"\n{request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    print(f"{response.status_code} - {process_time:.2f}ms")
    
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    
    return response


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler para errores de validación
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="ValidationError",
            message="Error de validación en los datos enviados",
            timestamp=get_timestamp(),
            details={
                "errors": exc.errors(),
                "body": exc.body
            }
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handler para excepciones generales no capturadas.
    """
    print(f"Error no manejado: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="Error interno del servidor",
            timestamp=get_timestamp(),
            details={"error_type": type(exc).__name__}
        ).model_dump()
    )


# ============================================================================
# ROUTES
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raíz de la API.
    
    Returns:
        dict: Mensaje de bienvenida y enlaces útiles
    """
    return {
        "message": "Bienvenido al Chatbot de IA con RAG",
        "description": "API especializada en Inteligencia Artificial",
        "version": settings["version"],
        "documentation": {
            "swagger_ui": settings["docs_url"],
            "redoc": settings["redoc_url"]
        },
        "endpoints": {
            "chat": f"{settings['api_prefix']}/chat",
            "health": f"{settings['api_prefix']}/health",
            "stats": f"{settings['api_prefix']}/stats",
            "info": f"{settings['api_prefix']}/info"
        },
    }

app.include_router(auth.router, prefix=settings["api_prefix"])  
app.include_router(chat.router, prefix=settings["api_prefix"])
app.include_router(system.router, prefix=settings["api_prefix"])
app.include_router(metrics.router, prefix=settings["api_prefix"])
app.include_router(documents.router, prefix=settings["api_prefix"])
app.include_router(whatsapp.router)  
app.include_router(telegram.router)  

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print("Iniciando servidor UVICORN")
    print("="*70 + "\n")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

