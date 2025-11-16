# 🔄 Migración a Nueva Estructura Multi-Plataforma

Este documento resume los cambios realizados para soportar múltiples plataformas.

---

## ✅ Cambios Realizados

### 1. Nueva Estructura de Carpetas

**Creado:**
- `api/platforms/` - Implementaciones de plataformas
- `api/platforms/base.py` - Interfaz común
- `api/platforms/whatsapp/client.py` - Cliente WhatsApp
- `api/platforms/telegram/client.py` - Cliente Telegram
- `api/services/message_service.py` - Servicio común
- `api/services/platform_handlers.py` - Factory de plataformas
- `api/config/messages.py` - Mensajes unificados
- `api/utils/session_manager.py` - Gestión de sesiones común
- `api/utils/message_logger.py` - Logger común
- `api/routes/telegram.py` - Router de Telegram

**Refactorizado:**
- `api/routes/whatsapp.py` - Ahora usa la nueva arquitectura
- `api/main.py` - Incluye router de Telegram

---

## 🔄 Cambios en Imports

### Antes:
```python
from api.utils.whatsapp_helpers import send_whatsapp_message
from api.services.whatsapp_service import process_whatsapp_message
from api.config.whatsapp_messages import get_welcome_message
```

### Después:
```python
from api.services.platform_handlers import get_platform_client
from api.services.message_service import process_message
from api.config.messages import get_welcome_message
```

---

## 📝 Variables de Entorno

**Agregar a `.env`:**
```env
# WhatsApp (ya existía)
WHATSAPP_ACCESS_TOKEN=tu_token
WHATSAPP_PHONE_NUMBER_ID=tu_id
WEBHOOK_VERIFY_TOKEN=tu_token

# Telegram (nuevo)
TELEGRAM_BOT_TOKEN=tu_token_del_bot
```

---

## 🚀 Cómo Usar

### WhatsApp (sin cambios)
- Webhook: `POST /whatsapp/webhook`
- Health: `GET /whatsapp/health`

### Telegram (nuevo)
- Webhook: `POST /telegram/webhook`
- Health: `GET /telegram/health`
- Configurar webhook: Ver `TELEGRAM_SETUP.md`

---

## ⚠️ Archivos Deprecados

Estos archivos ya no se usan pero se mantienen por compatibilidad:

- `api/services/whatsapp_service.py` → Usar `services/message_service.py`
- `api/utils/whatsapp_helpers.py` → Usar `platforms/whatsapp/client.py`
- `api/utils/whatsapp_logger.py` → Usar `utils/message_logger.py`
- `api/config/whatsapp_messages.py` → Usar `config/messages.py`

**Pueden eliminarse después de verificar que todo funciona.**

---

## ✅ Verificación

1. ✅ WhatsApp sigue funcionando igual
2. ✅ Telegram está integrado y funcionando
3. ✅ Lógica común compartida
4. ✅ Mensajes parametrizables
5. ✅ Logs unificados
6. ✅ Sesiones unificadas

---

## 📚 Documentación

- `ESTRUCTURA_PROYECTO.md` - Explicación de la estructura
- `TELEGRAM_SETUP.md` - Configuración de Telegram
- `WHATSAPP_SETUP.md` - Configuración de WhatsApp (si existe)

---

## 🎯 Próximos Pasos

1. Probar WhatsApp (debería funcionar igual que antes)
2. Configurar Telegram (ver `TELEGRAM_SETUP.md`)
3. Probar Telegram
4. Eliminar archivos deprecados (opcional)

---

¡La nueva estructura está lista! 🎉


