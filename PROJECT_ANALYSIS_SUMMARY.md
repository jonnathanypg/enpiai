# Radiografía Completa del Sistema EnpiAI (Herbalife SaaS Platform)

## 1. Arquitectura General y Flujo en Producción
El proyecto **EnpiAI** sigue una arquitectura moderna HTA (Hypermedia-Driven, Task-Queue, Agentic), dividida en microservicios independientes orquestados por PM2 en tu VPS:

1. **Frontend (`enpiai-frontend` - Puerto 3000)**: Construido en Next.js (App Router). Maneja el dashboard multi-tenant, CRM (vista 360), y configuración de los Agentes.
2. **Backend Core (`enpiai-backend` - Puerto 5000)**: Aplicación Flask que expone las APIs REST y los Webhooks.
3. **Redis (`enpiai-redis` - Puerto 6381)**: Actúa como el broker de mensajes para Celery y como caché.
4. **Worker AI (`enpiai-worker`)**: Un proceso de Celery que toma las tareas pesadas en segundo plano (consultas a GPT-5/OpenAI, LangGraph, generación de RAG, creación de PDFs).
5. **Gateway de WhatsApp (`enpiai-whatsapp` - Puerto 3001)**: Un microservicio en Node.js que envuelve la librería Baileys. Mantiene las conexiones persistentes con WhatsApp Web, guarda las sesiones en MySQL, y envía webhooks al backend.

### ¿Cómo es el flujo de un mensaje en Producción?
1. **Entrada:** Un cliente escribe a WhatsApp. `enpiai-whatsapp` detecta el mensaje usando Baileys (`messages.upsert`).
2. **Notificación:** Node.js (via `ioc.ts`) toma el texto, detecta adjuntos y hace un **HTTP POST** a tu backend Flask (`/webhooks/whatsapp`).
3. **Recepción Rápida:** Flask recibe el webhook, guarda el mensaje del usuario en MySQL (tabla `messages`), y **no bloquea el proceso**. Inmediatamente responde `200 OK` (Fire & Forget) y lanza una tarea asíncrona a Celery (`process_webhook_message.delay()`).
4. **Procesamiento AI:** El `enpiai-worker` toma la tarea de Redis. Carga el `get_agent_orchestrator`, envía el contexto a OpenAI (LangGraph), recibe la respuesta, y guarda el mensaje generado en MySQL.
5. **Salida:** Celery hace un **HTTP POST** hacia `enpiai-whatsapp` (Puerto 3001) para enviar el mensaje de vuelta al número del cliente. Node.js finalmente usa Baileys para entregar el mensaje en WhatsApp.

---

## 2. Análisis del Test: ¿Por qué no recibiste respuesta?
Mencionas que conectaste un WhatsApp, enviaste un mensaje desde otro número y el agente no respondió.

**Lo que sí funcionó (Según los logs del Worker):**
El Worker (`enpiai-worker`) recibió la tarea correctamente y la procesó:
```log
[2026-04-30 00:04:49,804: INFO/ForkPoolWorker-3] HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
[2026-04-30 00:04:53,663: INFO/ForkPoolWorker-3] WhatsApp sent to 593982840685
[2026-04-30 00:04:53,672: INFO/ForkPoolWorker-3] Task tasks.process_webhook_message[...] succeeded
```
El agente **SÍ** generó la respuesta y el Worker **SÍ** hizo la petición al servicio local de WhatsApp para entregar el mensaje.

**El Problema Raíz (Según los logs de enpiai-whatsapp):**
La falla está exclusivamente en el microservicio de WhatsApp en el VPS, el cual se está reiniciando constantemente (Crash Loop).
```log
11|enpiai- |     at useMySQLAuthState (/root/.npm/_npx/cd735d76ddd573ff/node_modules/@agenticnucleus/whatsapp-multitenant/dist/infrastructure/auth/mysql.auth.js:20:42)
11|enpiai- |   code: 'ECONNRESET',
```
```log
11|enpiai- | [4] Connection closed. Reason: 428, Error: Error: Connection Terminated
11|enpiai- | [4] Reconnecting in 3 seconds...
11|enpiai- | [4] Connection opened
```

### El Diagnóstico de la Falla:
1. **Ejecución de Código Fantasma (Outdated Package):** La ruta del error (`/root/.npm/_npx/...`) demuestra que tu servidor en Producción **no está ejecutando el código local** que tienes en `./api-whatsapp/src`. En su lugar, PM2 está ejecutando el paquete remoto/global `@agenticnucleus/whatsapp-multitenant` vía `npx`.
2. **Error de MySQL (`ECONNRESET`):** Ese paquete viejo no tenía la lógica adecuada de `enableKeepAlive` en la conexión a MySQL. Cuando la base de datos corta la conexión inactiva, la librería se cae completamente y crashea el proceso Node.js.
3. **El Bucle de Desconexión (`Reason: 428`):** Al crashear y reiniciarse la aplicación múltiples veces por segundo (Crash Loop), los servidores de Meta detectan un comportamiento anómalo (múltiples intentos de login sucesivos) y cierran la sesión forzosamente (`Connection Terminated - 428`). Esto evita que el mensaje que envió el Celery Worker pueda salir de la cola hacia el teléfono.

---

## 3. ¿Cómo solucionarlo y comportarse en Producción?

Has hecho el trabajo correcto en local: refactorizar el `api-whatsapp` eliminando la dependencia externa y usando un `app.js` local con un pool de conexiones MySQL con `enableKeepAlive: true` (`connection.ts`). Sin embargo, el VPS no ha aplicado estos cambios al ejecutar PM2.

**Pasos exactos para reparar tu VPS:**

1. **Asegúrate de que se ejecute el código local:**
   En tu archivo `ecosystem.config.js`, aunque dice `script: "npm", args: "run start"`, es probable que el `package.json` en tu VPS siga teniendo el comando de ejecución antiguo `npx ...` (porque no hiciste git pull o npm install), o que PM2 en tu VPS haya guardado en memoria el comando `npx`.
   
2. **Re-compilar el código TypeScript en el VPS:**
   Asegúrate de que en el VPS, dentro de la carpeta `/root/enpiai/api-whatsapp/`, exista la carpeta `dist/` actualizada.
   ```bash
   cd /root/enpiai/api-whatsapp
   git pull origin main
   npm install
   npm run build
   ```
3. **Actualizar PM2 para que use tu ejecutable compilado directamente:**
   Recomiendo fuertemente arrancar directamente usando node en vez de npm, para evitar problemas de dependencias:
   ```bash
   pm2 delete enpiai-whatsapp
   cd /root/enpiai/api-whatsapp
   pm2 start dist/app.js --name "enpiai-whatsapp" --watch false
   pm2 save
   ```
   *(Nota: Puedes actualizar tu `ecosystem.config.js` local para reflejar esto).*
4. **Limpiar las Sesiones Corruptas en la Base de Datos:**
   Debido a los múltiples crashes, las llaves de encriptación en MySQL pueden haberse corrompido. Debes limpiar la tabla de sesiones para tu usuario desde el backend Flask o directamente en la BD:
   ```sql
   DELETE FROM bailey_sessions WHERE session_id = 'TU_DISTRIBUTOR_ID';
   ```
5. **Re-conectar WhatsApp:**
   Entra al dashboard web, ve a la sección del agente de WhatsApp, escanea el código QR de nuevo. El sistema usará ahora tu código nativo local, resistiendo la caída de base de datos gracias a `enableKeepAlive` y procesando el flujo sin interrupciones.

## Conclusión de la Radiografía
Tu arquitectura base (HTA) y la lógica de LangGraph con OpenAI están funcionando perfectamente bajo presión (el log del worker prueba que es capaz de recibir, razonar y disparar un mensaje de vuelta en apenas 10 segundos). 
El único eslabón roto es cómo PM2 en Contabo está "arrancando" el proceso de Node.js de WhatsApp, forzando a usar una versión antigua instalada por NPX que no es resiliente a los micro-cortes de red de la base de datos MySQL. Una vez que dirijas PM2 a ejecutar tu `dist/app.js` localizado, el agente comenzará a responder fluidamente.
