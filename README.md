# Chatbot IA con Gemini

Chatbot especializado en Inteligencia Artificial que utiliza la API de Gemini para responder preguntas. 
Incluye sistema de logging para monitorear el rendimiento, uso de tokens y costos de las llamadas a la API.

## Requisitos

- Python 3.11 o superior

## Instalación

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
