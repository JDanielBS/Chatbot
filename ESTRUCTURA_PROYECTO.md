# 📁 Estructura del Proyecto - Arquitectura Multi-Plataforma

Este documento explica la nueva estructura del proyecto que soporta múltiples plataformas de mensajería (WhatsApp, Telegram, etc.).

---

## 🏗️ Estructura Completa

```
api/
├── routes/                    # Endpoints HTTP (FastAPI routers)
│   ├── chat.py               # API REST para chat web
│   ├── system.py             # Health, stats, métricas
│   ├── whatsapp.py           # Webhook WhatsApp
│   └── telegram.py           # Webhook Telegram
│
├── services/                  # Lógica de negocio
│   ├── message_service.py    # ⭐ Servicio COMÚN de procesamiento
│   ├── platform_handlers.py  # Factory para obtener clientes de plataformas
│   └── whatsapp_service.py  # ⚠️ DEPRECADO (usar message_service.py)
│
├── platforms/                # Implementaciones de plataformas
│   ├── base.py               # ⭐ Clase abstracta PlatformClient
│   ├── whatsapp/
│   │   ├── client.py         # Cliente WhatsApp Business API
│   │   └── __init__.py
│   └── telegram/
│       ├── client.py         # Cliente Telegram Bot API
│       └── __init__.py
│
├── config/                    # Configuración
│   ├── messages.py           # ⭐ Mensajes COMUNES (parametrizables)
│   └── __init__.py
│
├── utils/                     # Utilidades
│   ├── session_manager.py    # ⭐ Gestión de sesiones (común)
│   ├── message_logger.py     # ⭐ Logger común (todas las plataformas)
│   ├── whatsapp_helpers.py  # ⚠️ DEPRECADO (usar platforms/whatsapp/client.py)
│   └── whatsapp_logger.py   # ⚠️ DEPRECADO (usar message_logger.py)
│
├── dependencies.py           # Singletons (RAG, LLM, Chain)
├── models.py                 # Modelos Pydantic
└── main.py                   # Aplicación FastAPI principal
```

---

## 🎯 Principios de Diseño

### 1. **Separación de Responsabilidades**

| Capa | Responsabilidad |
|------|-----------------|
| **routes/** | Solo endpoints HTTP, parsing de webhooks |
| **services/** | Lógica de negocio común (comandos, RAG, LLM) |
| **platforms/** | Implementación específica de cada plataforma |
| **config/** | Configuración parametrizable (mensajes, etc.) |
| **utils/** | Utilidades compartidas (sesiones, logs) |

### 2. **Interfaz Común (PlatformClient)**

Todas las plataformas implementan la misma interfaz:

```python
class PlatformClient(ABC):
    def send_message(user_id, message) -> bool
    def mark_as_read(message_id) -> None
    def extract_message_data(webhook_data) -> dict
    def get_platform_name() -> str
```

**Ventaja**: Puedes agregar nuevas plataformas sin cambiar la lógica de negocio.

### 3. **Lógica Común Compartida**

- ✅ Procesamiento de mensajes → `services/message_service.py`
- ✅ Gestión de sesiones → `utils/session_manager.py`
- ✅ Logging → `utils/message_logger.py`
- ✅ Mensajes → `config/messages.py`

**Ventaja**: Un solo lugar para mantener la lógica, funciona para todas las plataformas.

---

## 📦 Módulos Principales

### `api/services/message_service.py`

**Responsabilidad**: Procesar mensajes de cualquier plataforma.

```python
# Usa la misma lógica para WhatsApp y Telegram
response = await process_message(
    platform="whatsapp",  # o "telegram"
    user_id="123456789",
    message_text="¿Qué es la IA?",
    message_id="msg_123"
)
```

**Funciones principales:**
- `process_message()` - Procesa comandos y preguntas
- `get_sources_message()` - Obtiene lista de fuentes
- `_process_ai_question()` - Procesa con RAG y LLM

---

### `api/platforms/base.py`

**Responsabilidad**: Define la interfaz común.

Todas las plataformas deben implementar:
- `send_message()` - Enviar mensaje
- `mark_as_read()` - Marcar como leído
- `extract_message_data()` - Extraer datos del webhook
- `get_platform_name()` - Nombre de la plataforma

---

### `api/platforms/whatsapp/client.py`

**Responsabilidad**: Implementación específica de WhatsApp.

- Usa WhatsApp Business API
- Maneja formato de webhook de Meta
- Implementa `mark_as_read()` (WhatsApp lo soporta)

---

### `api/platforms/telegram/client.py`

**Responsabilidad**: Implementación específica de Telegram.

- Usa Telegram Bot API
- Maneja formato de webhook de Telegram
- `mark_as_read()` no hace nada (Telegram no lo soporta)

---

### `api/utils/session_manager.py`

**Responsabilidad**: Gestión unificada de sesiones.

```python
# Funciona para cualquier plataforma
session = get_session("whatsapp", "573233207683")
session = get_session("telegram", "123456789")
```

**Características:**
- Hash anonimizado del usuario
- Soporta múltiples plataformas
- Thread ID único por sesión

---

### `api/config/messages.py`

**Responsabilidad**: Mensajes parametrizables.

**Ventajas:**
- ✅ Fácil de modificar
- ✅ Un solo lugar para todos los mensajes
- ✅ Funciona para todas las plataformas
- ✅ Variables configurables (institución, nombre del bot)

---

## 🔄 Flujo de un Mensaje

### Ejemplo: Usuario envía "¿Qué es la IA?" por WhatsApp

```
1. WhatsApp → Webhook POST /whatsapp/webhook
   ↓
2. api/routes/whatsapp.py → receive_message()
   ↓
3. WhatsAppClient.extract_message_data() → Extrae datos
   ↓
4. WhatsAppClient.mark_as_read() → Marca como leído
   ↓
5. services/message_service.py → process_message()
   ↓
6. get_session("whatsapp", user_id) → Obtiene/crea sesión
   ↓
7. Procesa comandos o pregunta con RAG/LLM
   ↓
8. log_interaction() → Guarda log anonimizado
   ↓
9. WhatsAppClient.send_message() → Envía respuesta
   ↓
10. Usuario recibe respuesta ✅
```

---

## ➕ Agregar una Nueva Plataforma

### Paso 1: Crear cliente

```python
# api/platforms/discord/client.py
from api.platforms.base import PlatformClient

class DiscordClient(PlatformClient):
    def send_message(self, user_id: str, message: str) -> bool:
        # Implementar envío a Discord
        pass
    
    def mark_as_read(self, message_id: str) -> None:
        # Discord no tiene esto, dejar vacío
        pass
    
    def extract_message_data(self, webhook_data: dict):
        # Extraer datos del webhook de Discord
        pass
    
    def get_platform_name(self) -> str:
        return "discord"
```

### Paso 2: Registrar en factory

```python
# api/services/platform_handlers.py
from api.platforms.discord.client import DiscordClient

def get_platform_client(platform: str):
    if platform == "discord":
        return DiscordClient()
    # ... resto
```

### Paso 3: Crear router

```python
# api/routes/discord.py
from api.services.message_service import process_message
from api.services.platform_handlers import get_platform_client

@router.post("/webhook")
async def receive_message(request: Request):
    client = get_platform_client("discord")
    message_data = client.extract_message_data(await request.json())
    # ... procesar igual que WhatsApp/Telegram
```

### Paso 4: Registrar en main.py

```python
# api/main.py
from api.routes import discord
app.include_router(discord.router)
```

**¡Listo!** La nueva plataforma usa toda la lógica común automáticamente.

---

## 📊 Ventajas de esta Estructura

| Ventaja | Descripción |
|---------|-------------|
| **Escalable** | Fácil agregar nuevas plataformas |
| **DRY** | Lógica común no se duplica |
| **Mantenible** | Cada plataforma en su módulo |
| **Testeable** | Fácil mockear plataformas |
| **Flexible** | Cada plataforma puede tener lógica específica |
| **Parametrizable** | Mensajes fáciles de modificar |

---

## 🔍 Archivos Deprecados (Mantener por compatibilidad)

Estos archivos ya no se usan pero se mantienen temporalmente:

- `api/services/whatsapp_service.py` → Usar `services/message_service.py`
- `api/utils/whatsapp_helpers.py` → Usar `platforms/whatsapp/client.py`
- `api/utils/whatsapp_logger.py` → Usar `utils/message_logger.py`
- `api/config/whatsapp_messages.py` → Usar `config/messages.py`

**Nota**: Pueden eliminarse después de verificar que todo funciona.

---

## 📝 Convenciones

1. **Nombres de archivos**: `snake_case.py`
2. **Nombres de clases**: `PascalCase`
3. **Nombres de funciones**: `snake_case`
4. **Plataformas**: siempre en minúsculas (`"whatsapp"`, `"telegram"`)

---

## 🎯 Resumen

- ✅ **Arquitectura modular** con separación clara de responsabilidades
- ✅ **Interfaz común** para todas las plataformas
- ✅ **Lógica compartida** para evitar duplicación
- ✅ **Fácil de extender** con nuevas plataformas
- ✅ **Mensajes parametrizables** en un solo lugar

Esta estructura permite escalar fácilmente a más plataformas (Discord, Slack, etc.) sin modificar la lógica de negocio.


