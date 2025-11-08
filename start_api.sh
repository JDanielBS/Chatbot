# Script para iniciar la API del Chatbot de IA (Linux/Mac
echo "========================================"
echo " CHATBOT IA - INICIANDO API"
echo "========================================"
echo ""

# Verificar que existe el .env
if [ ! -f .env ]; then
    echo "[ERROR] No se encontró el archivo .env"
    echo "Por favor crea un archivo .env con:"
    echo "  GEMINI_API_KEY=tu_clave_aqui"
    echo ""
    exit 1
fi

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "Activando entorno virtual..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Activando entorno virtual..."
    source .venv/bin/activate
else
    echo "[ADVERTENCIA] No se encontró entorno virtual"
    echo "Usando Python global..."
fi

echo ""
echo "Instalando/actualizando dependencias..."
pip install -r requirements.txt --quiet

echo ""
echo "========================================"
echo " Iniciando servidor FastAPI..."
echo "========================================"
echo ""
echo "  Documentación: http://localhost:8000/docs"
echo "  Health Check:  http://localhost:8000/api/health"
echo "  Chat:          http://localhost:8000/api/chat"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo "========================================"
echo ""

# Iniciar API
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

