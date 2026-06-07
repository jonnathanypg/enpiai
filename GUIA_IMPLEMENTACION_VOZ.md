# 🎙️ Guía de Implementación de Voz - EnpiAI

**Proyecto:** Herbalife Distributor SaaS Platform (EnpiAI)
**Tecnología:** FastAPI (Bridge) + Flask (Models) + Next.js 16 (React 19)

Esta guía detalla los pasos para integrar el **Protocolo Maestro de Voz IAGS** específicamente en el ecosistema de EnpiAI, permitiendo que los distribuidores de Herbalife interactúen mediante voz con sus agentes de IA.

---

## 1. Preparación del Backend (Python/FastAPI)

### A. Nuevo Servicio: `services/voice_service.py`
Se debe crear este servicio copiando la lógica base de KindiCoreAI, adaptándola para usar las variables de entorno de EnpiAI:
*   `VOICE_STT_ENGINE`: Preferir `openai` (Whisper).
*   `OPENAI_API_KEY`: Requerido para Whisper.
*   `EDGE_TTS`: Motor para síntesis de voz neural.

### B. Directorio de Almacenamiento
Asegurar la existencia de la carpeta de uploads:
`enpiai/backend/uploads/voice/`

### C. Nuevos Endpoints en FastAPI (`fastapi_app.py` o `routes/voice.py`)
Implementar:
*   `POST /api/voice/interact`: Recibe audio, transcribe, procesa con LangGraph y retorna audio de respuesta.
*   `POST /api/voice/synthesize`: Síntesis bajo demanda para el Chat Web.
*   `GET /api/voice/voices`: Listado de voces (Filtro por `es-EC` o locales).

---

## 2. Integración con WhatsApp (`api-whatsapp`)

### A. Webhook de Entrada
Actualizar el webhook en el backend (`backend/routes/webhooks.py` o donde se maneje WhatsApp) para detectar adjuntos de tipo `audio`.
*   **Lógica:** Si llega un audio, descargar el archivo temporalmente, pasarlo por `VoiceService.transcribe()` y usar el texto resultante como el `message` principal.

### B. Respuesta por Audio
Si la entrada fue un audio, el Agente debe generar su respuesta y luego:
1.  Sintetizar el texto de respuesta a MP3.
2.  Enviar el MP3 mediante `POST /lead/media` (mediaType: 'audio') del microservicio WhatsApp.

---

## 3. Frontend (Next.js 16 / React 19)

### A. Actualización de `ChatWidget.tsx`
Integrar las capacidades de grabación y reproducción:
*   **Micrófono:** Usar `MediaRecorder` API para capturar `audio/webm`.
*   **Modo Voz:** Switch para activar el "Speaker".
*   **Efecto Typewriter + Audio:** Sincronizar la aparición del texto con la reproducción del audio si es posible, o simplemente reproducir al recibir la respuesta.

### B. Desbloqueo de Audio (Políticas de Autoplay)
Implementar la función `unlockAudio()` que se ejecute en el primer clic del usuario en la interfaz para permitir que la IA "hable" de forma asíncrona después.

---

## 4. Configuración de Identidad (IdentityResolver)
EnpiAI utiliza `IdentityResolver` para diferenciar entre Distribuidores y Clientes. La implementación de voz debe:
1.  Identificar al Distribuidor (Owner) para usar su configuración de voz personalizada.
2.  Identificar al Cliente para mantener el historial de la conversación (memoria de LangGraph) vinculado a su teléfono.

---

## 5. Próximos Pasos (Checklist)
- [ ] Crear `services/voice_service.py`.
- [ ] Registrar Blueprint/Rutas de Voice en FastAPI.
- [ ] Modificar el webhook de WhatsApp para soportar `audio/transcription`.
- [ ] Actualizar el `ChatWidget` en el frontend con controles de audio.
- [ ] Configurar voz predeterminada (`es-EC-LuisNeural`) en el modelo de Agente.

---
**Nota:** No realizar cambios de código hasta que esta guía sea validada y se inicie la fase de ejecución.
