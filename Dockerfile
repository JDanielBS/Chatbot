# Dockerfile para el backend FastAPI
FROM python:3.11-slim

# Metadatos
LABEL maintainer="Chatbot IA - Universidad de Caldas"
LABEL description="Backend FastAPI con RAG y Gemini"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (para cache de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p data/chroma_db models metrics/message_logs

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Puerto dinámico para Railway
ENV PORT=8000

# Comando para iniciar la API (usa $PORT de Railway)
CMD python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT

