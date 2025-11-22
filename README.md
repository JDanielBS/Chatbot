# Chatbot IA con Gemini

Chatbot especializado en Inteligencia Artificial que utiliza la API de Gemini para responder preguntas. 
Incluye sistema de logging para monitorear el rendimiento, uso de tokens y costos de las llamadas a la API.

## Requisitos

### Para desarrollo local:
- Python 3.11 o superior
- Node.js 18+ (para el frontend)

### Para Docker (recomendado):
- Docker Desktop o Docker Engine 20.10+
- Docker Compose 2.0+

## Instalación

## 🐳 Opción 1: Usar Docker (Recomendado)

Esta es la forma más sencilla y reproducible de ejecutar el proyecto.

### Prerrequisitos
- Docker Desktop instalado y corriendo
- Archivo `.env` configurado (ver más abajo)

### Pasos rápidos

1. **Configurar variables de entorno**
   
   Crea un archivo `.env` en la raíz del proyecto:
   ```env
   GEMINI_API_KEY=tu_clave_aqui
   WHATSAPP_ACCESS_TOKEN=tu_token_si_tienes
   WHATSAPP_PHONE_NUMBER_ID=tu_phone_id_si_tienes
   TELEGRAM_BOT_TOKEN=tu_token_si_tienes
   ```

2. **Construir y levantar los contenedores**
   ```bash
   docker-compose up --build
   ```
   
   La primera vez puede tardar varios minutos (descarga de imágenes, instalación de dependencias, etc.)

3. **Acceder a la aplicación**
   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **Documentación Swagger**: http://localhost:8000/docs

### Comandos útiles de Docker

```bash
# Levantar servicios en segundo plano
docker-compose up -d

# Ver logs
docker-compose logs -f

# Ver logs solo del backend
docker-compose logs -f backend

# Detener servicios
docker-compose down

# Detener y eliminar volúmenes (borra ChromaDB y modelos)
docker-compose down -v

# Reconstruir solo el backend
docker-compose build backend

# Ejecutar comandos dentro del contenedor
docker-compose exec backend python load_new_docs.py
```

### Cargar documentos en Docker

Para cargar documentos a la base vectorial dentro del contenedor:

```bash
# Opción 1: Ejecutar el script dentro del contenedor
docker-compose exec backend python load_new_docs.py

# Opción 2: Copiar documentos y ejecutar
# Los documentos en ./data/new-docs/ se montan automáticamente
docker-compose exec backend python load_new_docs.py
```

### Notas sobre Docker

- **Persistencia de datos**: Los datos de ChromaDB, modelos y métricas se guardan en tu máquina local (volúmenes montados)
- **Variables de entorno**: Se cargan desde el archivo `.env` en la raíz del proyecto

---

## 💻 Opción 2: Instalación Local (Desarrollo)

### 1. Crear y activar un entorno virtual (recomendado)

```bash
# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1

# Windows (cmd)
python -m venv venv
venv\\Scripts\\activate.bat

# Linux / Mac
python -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto con tu clave de API de Gemini:

```
GEMINI_API_KEY=tu_clave_aqui
```

### 4. Preparar el modelo local (recomendado)

Antes de iniciar la API, es recomendable ejecutar el script `save_model.py` para preparar o descargar el modelo de embeddings localmente. Esto asegura que el modelo esté disponible en disco y evita descargas durante la indexación.

```bash
python save_model.py
```

El script guarda o prepara los artefactos del modelo en la carpeta `models/` (o la ruta que esté configurada en el script).

## Configuración inicial

### Cargar documentos a la base de conocimiento

Antes de usar el chatbot, debes cargar documentos a la base vectorial:

```bash
python load_new_docs.py
```

Este script carga todos los archivos `.txt` desde `data/new-docs/` y los indexa en la base vectorial ChromaDB.

## Ejecutar la API

### Opción 1: Usar el script batch (recomendado)

```bash
# Windows
start_api.bat

# Linux / Mac
bash start_api.sh
```

El script:
- Verifica que exista el archivo `.env`
- Activa el entorno virtual automáticamente
- Instala/actualiza dependencias
- Inicia el servidor FastAPI en `http://localhost:8000`

### Opción 2: Comando manual

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Endpoints disponibles

Una vez iniciada la API, puedes acceder a:

- **Documentación interactiva (Swagger)**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health
- **Chat**: http://localhost:8000/api/chat

## Exponer la API públicamente (ngrok)

Si necesitas usar los webhooks de WhatsApp o Telegram, debes exponer tu API local usando ngrok:

1. **Instalar ngrok**: Descarga desde https://ngrok.com/download

2. **Iniciar ngrok** (en una terminal separada):
   ```bash
   ngrok http 8000
   ```

3. **Copiar la URL pública**: ngrok te dará una URL como `https://xxxx-xx-xx-xx-xx.ngrok-free.app`

4. **Configurar webhooks**:
   - **WhatsApp**: Configura el webhook en tu cuenta de Meta Developers apuntando a: `https://tu-url-ngrok.ngrok-free.app/whatsapp/webhook`
   - **Telegram**: Configura el webhook usando la API de Telegram: 
     ```bash
     curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://tu-url-ngrok.ngrok-free.app/telegram/webhook"
     ```

## Notas importantes

- Asegúrate de tener el fichero `.env` con `GEMINI_API_KEY` antes de iniciar la API.
- Si vas a indexar muchos documentos, considera preparar el modelo localmente y usar GPU (si está disponible) para acelerar el cálculo de embeddings.
- **Con Docker**: Los datos se persisten automáticamente. Si eliminas los contenedores con `docker-compose down -v`, perderás la base vectorial.

## 🧪 Pruebas

### Verificar que todo funciona

1. **Health Check del Backend**:
   ```bash
   curl http://localhost:8000/api/health
   ```
   Debe responder con `{"status": "healthy", ...}`

2. **Probar el chat**:
   - Abre http://localhost:3000 en tu navegador
   - O usa la API directamente:
     ```bash
     curl -X POST http://localhost:8000/api/chat/ \
       -H "Content-Type: application/json" \
       -d '{"message": "¿Qué es la inteligencia artificial?", "thread_id": "test"}'
     ```

3. **Ver logs en tiempo real**:
   ```bash
   docker-compose logs -f
   ```
