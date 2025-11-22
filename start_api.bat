@echo off
REM 

echo ========================================
echo  CHATBOT  - INICIANDO API
echo ========================================
echo.

REM Verificar que existe el .env
if not exist .env (
    echo [ERROR] No se encontro el archivo .env
    echo Por favor crea un archivo .env con:
    echo   GEMINI_API_KEY=tu_clave_aqui
    echo.
    pause
    exit /b 1
)

REM Activar entorno virtual si existe
if exist venv\Scripts\activate.bat (
    echo Activando entorno virtual...
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    echo Activando entorno virtual...
    call .venv\Scripts\activate.bat
) else (
    echo [ADVERTENCIA] No se encontro entorno virtual
    echo Usando Python global...
)

echo.
echo Instalando/actualizando dependencias...
pip install -r requirements.txt --quiet

echo.
echo ========================================
echo  Iniciando servidor FastAPI...
echo ========================================
echo.
echo  Documentacion: http://localhost:8000/docs
echo  Health Check:  http://localhost:8000/api/health
echo  Chat:          http://localhost:8000/api/chat
echo.
echo Presiona Ctrl+C para detener el servidor
echo ========================================
echo.

REM Iniciar API
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

pause

