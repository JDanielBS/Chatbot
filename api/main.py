"""
Aplicación principal FastAPI para el Chatbot de IA con RAG.

Este es el punto de entrada de la API REST que proporciona endpoints
para interactuar con el chatbot especializado en Inteligencia Artificial.

Características:
- Chat conversacional con RAG
- Memoria persistente de conversaciones
- Citación automática de fuentes
- Métricas de rendimiento
- Comparación de múltiples modelos

"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time

from api.models import ErrorResponse
from api.routes import chat, system, whatsapp, telegram, metrics
from api.dependencies import (
    get_settings,
    get_rag_manager,
    get_llm_gemini,
    get_chain,
    get_timestamp
)


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
        # Inicializar componentes singleton
        print("\nInicializando componentes...")
        
        # RAG Manager
        rag = get_rag_manager()
        stats = rag.get_stats()
        print(f"   RAG Manager: {stats.get('total_chunks', 0)} chunks cargados")
        
        # LLM
        llm = get_llm_gemini()
        print(f"   Gemini LLM: Listo")
        
        # Chain
        chain = get_chain()
        print(f"   LangGraph Chain: Con memoria persistente")
        
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
    
    yield  # Aquí la app está corriendo
    
    # SHUTDOWN
    print("\n" + "="*70)
    print("CERRANDO API DEL CHATBOT DE IA")
    print("="*70)
    print("   Limpiando recursos...")
    # Aquí se pueden agregar limpiezas si es necesario
    print("   ✅ Recursos liberados")
    print("="*70 + "\n")


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
    
    # Log de entrada
    print(f"\n{request.method} {request.url.path}")
    
    # Procesar request
    response = await call_next(request)
    
    # Log de salida
    process_time = (time.time() - start_time) * 1000
    print(f"{response.status_code} - {process_time:.2f}ms")
    
    # Agregar header con tiempo de procesamiento
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

# Root endpoint
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
        "status": "operational"
    }


# Incluir routers
app.include_router(chat.router, prefix=settings["api_prefix"])
app.include_router(system.router, prefix=settings["api_prefix"])
app.include_router(metrics.router, prefix=settings["api_prefix"])
app.include_router(whatsapp.router)  # WhatsApp sin prefix para webhook directo
app.include_router(telegram.router)  # Telegram sin prefix para webhook directo  

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

