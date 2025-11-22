# Chatbot IA con Gemini

Chatbot especializado en Inteligencia Artificial que utiliza la API de Gemini para responder preguntas. 
Incluye sistema de logging para monitorear el rendimiento, uso de tokens y costos de las llamadas a la API.

## Requisitos

- Python 3.11
- Archivo `.env` con la API key de Gemini, puesta como `GEMINI_API_KEY=clave_numérica`

## Instalación

Para instalar las dependencias necesarias, ejecute:

```bash
pip install -r requirements.txt
```
 
## Guardar / preparar el modelo local

Antes de iniciar la API es recomendable ejecutar el script `save_model.py` si quieres preparar o descargar el modelo de embeddings localmente. Esto asegura que el modelo esté disponible en disco y evita descargas durante la indexación.

Ejemplo:

```bash
python save_model.py
```

El script `save_model.py` guarda o prepara los artefactos del modelo en la carpeta `models/` (o la ruta que esté configurada en el script).

## Iniciar el proyecto / API

1. Crear y activar un entorno virtual (recomendado):

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

2. Instalar dependencias (si no lo hiciste antes):

```bash
pip install -r requirements.txt
```

3. Ejecutar `save_model.py` para descargar/preparar el modelo local:

```bash
python save_model.py
```

4. Iniciar la API:

```bash
# Usando el script de la plataforma (Windows)
start_api.bat

# Usando el script (Linux/Mac)
bash start_api.sh

# O ejecutar Uvicorn directamente
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

5. Documentación interactiva (una vez iniciada la API):

```
http://localhost:8000/docs
```

### Notas finales
- Asegúrate de tener el fichero `.env` con `GEMINI_API_KEY` antes de iniciar la API.
- Si vas a indexar muchos documentos, considera preparar el modelo localmente y usar GPU (si está disponible) para acelerar el cálculo de embeddings.
