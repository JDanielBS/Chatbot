# 🐳 Guía de Docker - Chatbot IA

Esta guía te explica cómo usar Docker para ejecutar el proyecto completo.

## 📋 Prerrequisitos

1. **Docker Desktop** instalado y corriendo
   - Windows/Mac: Descarga desde [docker.com](https://www.docker.com/products/docker-desktop)
   - Linux: Instala Docker Engine y Docker Compose

2. **Archivo `.env`** configurado en la raíz del proyecto
   ```env
   GEMINI_API_KEY=tu_clave_aqui
   # Opcional (para WhatsApp/Telegram):
   WHATSAPP_ACCESS_TOKEN=tu_token
   WHATSAPP_PHONE_NUMBER_ID=tu_phone_id
   TELEGRAM_BOT_TOKEN=tu_token
   ```

## 🚀 Inicio Rápido

### 1. Construir y levantar los servicios

```bash
docker-compose up --build
```

**Primera vez**: Esto puede tardar 5-10 minutos porque:
- Descarga las imágenes base (Python, Node.js, nginx)
- Instala todas las dependencias de Python
- Instala dependencias de Node.js
- Compila el frontend React
- Descarga modelos de embeddings (si no están en `models/`)

### 2. Verificar que todo funciona

Abre tu navegador y visita:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

### 3. Cargar documentos (primera vez)

Si es la primera vez, necesitas cargar documentos a la base vectorial:

```bash
docker-compose exec backend python load_new_docs.py
```

Esto cargará todos los `.txt` desde `data/new-docs/` a ChromaDB.

## 📝 Comandos Útiles

### Gestión de contenedores

```bash
# Levantar servicios en segundo plano
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f

# Ver logs solo del backend
docker-compose logs -f backend

# Ver logs solo del frontend
docker-compose logs -f frontend

# Detener servicios
docker-compose stop

# Detener y eliminar contenedores
docker-compose down

# Detener, eliminar contenedores Y volúmenes (⚠️ borra datos)
docker-compose down -v
```

### Reconstruir servicios

```bash
# Reconstruir todo
docker-compose build --no-cache

# Reconstruir solo el backend
docker-compose build backend

# Reconstruir solo el frontend
docker-compose build frontend

# Reconstruir y levantar
docker-compose up --build
```

### Ejecutar comandos dentro de los contenedores

```bash
# Ejecutar script de carga de documentos
docker-compose exec backend python load_new_docs.py

# Abrir shell interactivo en el backend
docker-compose exec backend bash

# Verificar Python y dependencias
docker-compose exec backend python --version
docker-compose exec backend pip list

# Verificar Node.js en frontend (si necesitas)
docker-compose exec frontend sh
```

### Verificar estado

```bash
# Ver estado de los servicios
docker-compose ps

# Ver uso de recursos
docker stats

# Verificar health checks
docker-compose ps
# Deberías ver "healthy" en la columna STATUS
```

## 🔧 Solución de Problemas

### El backend no inicia

1. **Verifica los logs**:
   ```bash
   docker-compose logs backend
   ```

2. **Verifica que el archivo `.env` existe**:
   ```bash
   cat .env
   ```

3. **Verifica que el puerto 8000 no esté en uso**:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # Linux/Mac
   lsof -i :8000
   ```

### El frontend no se conecta al backend

1. **Verifica que el backend esté corriendo**:
   ```bash
   curl http://localhost:8000/api/health
   ```

2. **Verifica la URL en el frontend**:
   - El frontend está configurado para usar `http://localhost:8000`
   - Si cambias el puerto del backend, debes reconstruir el frontend:
     ```bash
     # Edita docker-compose.yml y cambia REACT_APP_API_URL
     docker-compose build frontend
     docker-compose up -d frontend
     ```

### Error de permisos en Windows

Si tienes problemas con permisos al montar volúmenes:

1. Abre Docker Desktop
2. Ve a Settings → Resources → File Sharing
3. Asegúrate de que la unidad donde está el proyecto esté compartida

### Los modelos no se descargan

Los modelos de embeddings se guardan en `./models/` en tu máquina local.

Si quieres forzar la descarga dentro del contenedor:

```bash
docker-compose exec backend python save_model.py
```

### ChromaDB no persiste datos

Verifica que el volumen esté montado correctamente:

```bash
# Ver volúmenes montados
docker-compose exec backend ls -la /app/data/chroma_db

# Verificar que existe en tu máquina
ls -la ./data/chroma_db
```

## 📦 Estructura de Volúmenes

Los siguientes directorios se montan como volúmenes (persisten en tu máquina):

- `./data/chroma_db` → Base vectorial ChromaDB
- `./models` → Modelos de embeddings descargados
- `./metrics` → Métricas y logs de interacciones
- `./data/new-docs` → Documentos para cargar (solo lectura)

## 🎯 Flujo de Trabajo Recomendado

### Desarrollo

1. **Primera vez**:
   ```bash
   # 1. Configurar .env
   cp .env.example .env  # (si existe)
   # Editar .env con tus API keys
   
   # 2. Construir y levantar
   docker-compose up --build
   
   # 3. Cargar documentos
   docker-compose exec backend python load_new_docs.py
   ```

2. **Desarrollo diario**:
   ```bash
   # Levantar servicios
   docker-compose up -d
   
   # Ver logs
   docker-compose logs -f
   
   # Detener al finalizar
   docker-compose down
   ```

### Producción/Demostración

```bash
# Construir imágenes optimizadas
docker-compose build --no-cache

# Levantar en segundo plano
docker-compose up -d

# Verificar que todo funciona
curl http://localhost:8000/api/health
```

## 🔍 Verificar que Todo Funciona

### Test 1: Health Check del Backend
```bash
curl http://localhost:8000/api/health
```
**Esperado**: `{"status": "healthy", ...}`

### Test 2: API de Chat
```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Qué es la IA?", "thread_id": "test"}'
```
**Esperado**: Respuesta JSON con `response`, `sources`, etc.

### Test 3: Frontend
1. Abre http://localhost:3000
2. Deberías ver la interfaz del chatbot
3. Escribe una pregunta y verifica que responda

### Test 4: Swagger
1. Abre http://localhost:8000/docs
2. Deberías ver la documentación interactiva de la API
3. Prueba el endpoint `/api/chat/` desde ahí

## 💡 Tips

- **Primera ejecución lenta**: Es normal, los modelos de embeddings son grandes (~500MB-2GB)
- **Persistencia**: Los datos se guardan automáticamente en tu máquina
- **Logs**: Usa `docker-compose logs -f` para debuggear
- **Recursos**: El backend puede usar bastante RAM (especialmente con modelos grandes)
- **Reconstruir**: Si cambias código, reconstruye con `docker-compose up --build`

## 🆘 ¿Necesitas Ayuda?

1. Revisa los logs: `docker-compose logs`
2. Verifica el estado: `docker-compose ps`
3. Revisa esta guía
4. Consulta el README.md principal

