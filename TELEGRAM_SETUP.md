# 📱 Configuración del Bot de Telegram

Este documento explica cómo configurar y usar el bot de Telegram integrado con la API FastAPI.

## ✅ Características

- ✅ **Integración con FastAPI**: El bot está integrado como router en la misma API
- ✅ **RAG habilitado**: Usa la misma infraestructura de RAG que la API web
- ✅ **Opt-in/Opt-out**: Sistema de consentimiento explícito (igual que WhatsApp)
- ✅ **Comandos especiales**: POLÍTICA, FUENTE(S), MODO BREVE/EXTENDIDO
- ✅ **Logs anonimizados**: No se guarda información personal (solo hash de sesión)
- ✅ **Memoria persistente**: Mantiene contexto de conversación por usuario

---

## 🔧 Configuración

### 1. Crear un Bot en Telegram

1. Abre Telegram y busca **@BotFather**
2. Envía el comando `/newbot`
3. Sigue las instrucciones:
   - Nombre del bot: `Chatbot IA Universidad de Caldas`
   - Username del bot: `ia_ucaldas_bot` (debe terminar en `bot`)
4. BotFather te dará un **token** (guárdalo)

### 2. Variables de Entorno

Agrega esta variable a tu archivo `.env`:

```env
# Telegram Bot API
TELEGRAM_BOT_TOKEN=tu_token_del_bot_aqui
```

### 3. Configurar Webhook

**Opción A: Usando ngrok (desarrollo)**

1. Inicia tu servidor FastAPI:
   ```bash
   python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. Inicia ngrok:
   ```bash
   ngrok http 8000
   ```

3. Configura el webhook (reemplaza `TU_TOKEN` y `TU_URL_NGROK`):
   ```bash
   curl "https://api.telegram.org/botTU_TOKEN/setWebhook?url=https://TU_URL_NGROK.ngrok-free.app/telegram/webhook"
   ```

**Opción B: Usando servidor en producción**

```bash
curl "https://api.telegram.org/botTU_TOKEN/setWebhook?url=https://tu-dominio.com/telegram/webhook"
```

### 4. Verificar Webhook

```bash
curl "https://api.telegram.org/botTU_TOKEN/getWebhookInfo"
```

Deberías ver:
```json
{
  "ok": true,
  "result": {
    "url": "https://tu-url.ngrok-free.app/telegram/webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

---

## 🚀 Uso del Bot

### Flujo de Interacción

1. **Primer mensaje**: El usuario recibe el mensaje de bienvenida con opt-in
2. **Opt-in**: El usuario debe escribir "ACEPTO" para continuar
3. **Preguntas**: El usuario puede hacer preguntas sobre IA
4. **Comandos**: El usuario puede usar comandos especiales en cualquier momento
5. **Opt-out**: El usuario puede escribir "SALIR" para dejar de usar el servicio

### Comandos Disponibles

| Comando | Descripción |
|---------|-------------|
| `ACEPTO` | Acepta usar el servicio (opt-in) |
| `SALIR` | Deja de usar el servicio (opt-out) |
| `POLÍTICA` o `POLITICA` | Muestra la política de uso completa |
| `FUENTE` o `FUENTES` o `FUENTE(S)` | Lista las fuentes confiables utilizadas |
| `MODO BREVE` | Cambia a respuestas cortas (2-3 frases) |
| `MODO EXTENDIDO` | Cambia a respuestas detalladas con citas |

### Ejemplo de Conversación

```
Usuario: Hola
Bot: Bienvenido al Chatbot de Inteligencia Artificial...
     [Mensaje de bienvenida con opt-in]

Usuario: ACEPTO
Bot: ✅ ¡Bienvenido! Ahora puedes hacer preguntas...

Usuario: ¿Qué es la IA?
Bot: [Respuesta detallada con RAG y citas de fuentes]

Usuario: MODO BREVE
Bot: ✅ Modo Breve activado...

Usuario: ¿Qué es la IA?
Bot: [Respuesta corta y concisa]

Usuario: FUENTES
Bot: Fuentes Confiables Utilizadas:
     • unesco_ai_ethics.pdf
     • ai-act-european-parliament.pdf
     ...

Usuario: SALIR
Bot: 👋 Sesión cerrada...
```

---

## 📊 Logs Anonimizados

Los logs se guardan en: `./metrics/message_logs/interactions.csv`

**Campos guardados (SIN información personal):**
- `timestamp`: Fecha y hora de la interacción
- `platform`: Plataforma usada (telegram, whatsapp)
- `session_hash`: Hash SHA256 del ID de usuario (primeros 16 caracteres)
- `message_length`: Longitud del mensaje (no el texto)
- `response_length`: Longitud de la respuesta
- `mode`: Modo usado (brief/extended)
- `query_number`: Número de consulta global
- `sources_found`: Número de fuentes encontradas

**NO se guarda:**
- ❌ ID de usuario real (chat_id)
- ❌ Texto completo de los mensajes
- ❌ Información personal identificable (PII)

---

## 🔍 Endpoints Disponibles

### Webhook (Telegram)
- `POST /telegram/webhook` - Recepción de mensajes
- `GET /telegram/webhook` - Información sobre configuración del webhook

### Health Check
- `GET /telegram/health` - Estado del servicio de Telegram

**Ejemplo de respuesta:**
```json
{
  "status": "ok",
  "telegram_configured": true,
  "active_sessions": 3,
  "timestamp": "2024-01-15T10:30:00"
}
```

---

## ⚠️ Solución de Problemas

### Error: "TELEGRAM_BOT_TOKEN no configurado"
- ✅ Verifica que tengas `TELEGRAM_BOT_TOKEN` en tu `.env`
- ✅ Reinicia el servidor después de agregar la variable

### Error: "Webhook not set"
- ✅ Configura el webhook usando `setWebhook` (ver arriba)
- ✅ Verifica que la URL sea HTTPS (Telegram requiere HTTPS)
- ✅ Verifica que el servidor esté corriendo

### No recibo mensajes del usuario
- ✅ Verifica que el webhook esté configurado correctamente
- ✅ Revisa los logs del servidor para ver errores
- ✅ Verifica que ngrok esté corriendo (si usas ngrok)

### El bot no responde después de "ACEPTO"
- ✅ Revisa los logs de la API para ver errores
- ✅ Verifica que `GEMINI_API_KEY` esté configurado
- ✅ Verifica que la base de datos vectorial tenga documentos indexados

---

## 📝 Notas Importantes

1. **Webhook vs Polling**: Este bot usa webhooks (más eficiente). Para desarrollo local, necesitas ngrok o un servidor público.
2. **HTTPS Requerido**: Telegram requiere HTTPS para webhooks. Usa ngrok o un servidor con SSL.
3. **Límites**: Telegram tiene límites de rate (30 mensajes/segundo por bot).
4. **Memoria**: Las sesiones se guardan en memoria. En producción, usa Redis o una base de datos.

---

## 🔄 Comparación: WhatsApp vs Telegram

| Característica | WhatsApp | Telegram |
|----------------|----------|----------|
| Webhook | ✅ Sí | ✅ Sí |
| Marcar como leído | ✅ Sí | ❌ No (no existe en API) |
| Formato de mensajes | Markdown básico | Markdown completo |
| Configuración webhook | Meta for Developers | BotFather + API |
| Requiere HTTPS | ✅ Sí | ✅ Sí |

---

## 📚 Recursos

- [Telegram Bot API Docs](https://core.telegram.org/bots/api)
- [BotFather](https://t.me/BotFather)
- [ngrok](https://ngrok.com/)

---

## ✅ Checklist de Configuración

- [ ] ✅ Bot creado en Telegram con BotFather
- [ ] ✅ Token obtenido y agregado a `.env`
- [ ] ✅ Variables de entorno configuradas
- [ ] ✅ API iniciada y funcionando
- [ ] ✅ ngrok corriendo (o servidor en producción)
- [ ] ✅ Webhook configurado con `setWebhook`
- [ ] ✅ Webhook verificado con `getWebhookInfo`
- [ ] ✅ Bot probado enviando mensaje de prueba

---

¡Listo! 🎉 Tu bot de Telegram está integrado y funcionando con RAG.


