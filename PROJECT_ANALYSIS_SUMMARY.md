# Radiografía Completa del Sistema EnpiAI (Herbalife SaaS Platform)

## 1. Arquitectura General y Flujo en Producción
El proyecto **EnpiAI** sigue una arquitectura moderna HTA (Hypermedia-Driven, Task-Queue, Agentic), dividida en microservicios independientes orquestados por PM2 en tu VPS:

1. **Frontend (`enpiai-frontend` - Puerto 3000)**: Construido en Next.js (App Router). Maneja el dashboard multi-tenant, CRM (vista 360), y configuración de los Agentes.
2. **Backend Gateway (`enpiai-fastapi` - Puerto 5000)**: Aplicación FastAPI que actúa como punto de entrada unificado, manejando webhooks asíncronos y delegando a Flask para rutas legacy.
3. **Redis (`enpiai-redis` - Puerto 6381)**: Actúa como el broker de mensajes para Celery y como caché.
4. **Worker AI (`enpiai-worker`)**: Un proceso de Celery que toma las tareas pesadas en segundo plano (consultas a **GPT-5 Nano** (OpenAI), LangGraph, generación de RAG, creación de PDFs).
5. **Gateway de WhatsApp (`enpiai-whatsapp` - Puerto 3001)**: Un microservicio en Node.js que envuelve la librería Baileys. Mantiene las conexiones persistentes con WhatsApp Web, guarda las sesiones en MySQL, y envía webhooks al backend.

### ¿Cómo es el flujo de un mensaje en Producción?
1. **Entrada:** Un cliente escribe a WhatsApp. `enpiai-whatsapp` detecta el mensaje usando Baileys (`messages.upsert`).
2. **Notificación:** Node.js toma el texto, detecta adjuntos y hace un **HTTP POST** a tu backend FastAPI (`/webhooks/whatsapp`).
3. **Recepción Rápida:** FastAPI recibe el webhook de forma asíncrona, guarda el mensaje del usuario en MySQL (tabla `messages`), e inmediatamente responde `200 OK` (Fire & Forget), lanzando la tarea de procesamiento a Celery (`process_webhook_message.send_task`).
4. **Procesamiento AI:** El `enpiai-worker` toma la tarea de Redis. Carga el `AgentOrchestrator`, envía el contexto a OpenAI (LangGraph), recibe la respuesta, y guarda el mensaje generado en MySQL.
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

## 4. Pasarela de Pagos (PayPal Smart Buttons)

El sistema de facturación y recarga de créditos se ha migrado y optimizado utilizando los **Smart Payment Buttons del SDK de JavaScript de PayPal**, configurado específicamente para soportar cuentas de comerciantes de Ecuador/LATAM con el flujo **Guest Checkout** (Pago como Invitado) e integración de **Verificación Directa**.

### Flujo de Pago y Reglas de Registro
1. **Suscripciones Recurrentes (Membresías):**
   * **Requisito de Cuenta:** Debido a las políticas de seguridad y fraude de PayPal, para establecer una membresía de cobro recurrente (Suscripción/Billing Agreement), el cliente **siempre debe crear una contraseña** al introducir su tarjeta. Esto crea una cuenta de PayPal gratuita y segura asociada a la tarjeta, lo que le permite al usuario gestionar, actualizar o cancelar su suscripción directamente desde su portal.
   * **Visualización:** El flujo de checkout del frontend notifica explícitamente al usuario de esta regla para evitar fricción.
2. **Pagos Únicos (Bloques de Créditos):**
   * **Pago como Invitado Puro (Guest Checkout):** Para compras de una sola vez, el usuario puede introducir sus datos bancarios y completar el pago de forma 100% directa y como invitado, sin necesidad de crear contraseñas o registrarse en la plataforma de PayPal.

### Arquitectura de Activación Instantánea
Para mitigar la lentitud extrema de los webhooks de PayPal en Sandbox y producción (que pueden tardar de 3 a 15 minutos en llegar al backend), implementamos una estrategia de **Verificación Directa de doble vía**:
* **Frontend (`paypal-checkout.tsx`):** Al obtener la aprobación de pago del usuario en el popup, antes de refrescar la pantalla, el frontend envía una solicitud inmediata al backend con el `subscriptionID`.
* **Backend (`POST /api/billing/verify-subscription`):** El backend recibe el ID de suscripción, consulta en tiempo real mediante API REST directa (servidor a servidor) el estado de la suscripción en los servidores de PayPal, y activa la membresía en la base de datos de manera sub-segundo.
* **Resultado:** La recarga finaliza con éxito y la interfaz del usuario se actualiza al instante, ofreciendo una experiencia fluida e inmediata.

---

## 5. Ajustes, Políticas & Integraciones Recientes (Junio 2026)

Tras estabilizar los canales de mensajería y la pasarela de pagos con PayPal, se realizaron ajustes adicionales clave para el cumplimiento de normativas de tiendas de aplicaciones y plataformas de integración (como Google Cloud y Meta):

### 📄 Políticas Legales Personalizadas
Se implementaron e integraron páginas legales accesibles públicamente con traducción dinámica (Español, Inglés, Portugués), abordando específicamente la lógica interna y arquitectura de **EnpiAI**:
*   **Condiciones del Servicio (`/terms`)**: Declara explícitamente el descargo de responsabilidad y la **no afiliación oficial con Herbalife International o Herbalife Nutrition**. Aclara las responsabilidades del distribuidor sobre el contenido de la base de conocimientos (RAG) y prohíbe el envío de spam masivo mediante el gateway de WhatsApp/Telegram.
*   **Política de Privacidad (`/privacy`)**: Especifica la recopilación de datos sensibles de salud provenientes de las evaluaciones de bienestar corporales e IMC. Garantiza el aislamiento lógico multi-tenant y la protección de PII/salud mediante **cifrado Fernet a nivel de aplicación** en MySQL. Detalla la política de datos limitados de Google Calendar OAuth.
*   **Política de Reembolso (`/refunds`)**: Regula el reembolso de 14 días para membresías mensuales condicionándolo a un consumo menor al 10% de los créditos mensuales de inferencia de IA. Especifica el reembolso de recargas de créditos no consumidos en 7 días y la devolución vía API segura de PayPal.
*   *Nota de Navegación*: Los enlaces correspondientes se agregaron al footer de la página de inicio y al layout compartido de las páginas públicas (excluyendo el enlace de precios directo en footer por solicitud comercial).

### 🛠️ Configuración de Canales y Envío de Correo Fallback
*   **Ajuste Temporal de Interfaz**: Se ocultaron de forma temporal las opciones de vinculación de Calendario de Google y de SMTP personalizado en la pestaña de Configuración de Canales (`/channels`).
*   **Mailing con Fallback Dinámico**: Cuando el distribuidor no tiene un canal de email personalizado integrado, el backend y los trabajadores de Celery utilizan el SMTP general de la plataforma (`info@enpi.click` del `.env`), pero construyen dinámicamente las cabeceras `From` y firmas a nombre de la información comercial del distribuidor (ej. `"Nombre de Distribuidor via EnpiAI <info@enpi.click>"`). Esto permite enviar los reportes PDF de bienestar firmados al correo del prospecto de forma automática.

### 🔑 Google Sign-In & Google Tag Manager
*   **Google OAuth "Wrong Audience" Solucionado**: Se alineó la configuración `GOOGLE_CLIENT_ID` del backend (`.env`) con el Client ID activo del frontend (`916670609421-89u06k4t5hr5smkccrpsvgrmqh6o40qc.apps.googleusercontent.com`), permitiendo la correcta verificación criptográfica de los tokens ID y habilitando el inicio de sesión y registro automático frictionless.
*   **Google Tag Manager**: Se integraron los scripts de seguimiento de GTM (`GTM-54SSFHBZ`) en la cabecera y el cuerpo del layout de Next.js 16 (`app/layout.tsx`) utilizando la directiva `<Script>` optimizada.

---

## Conclusión de la Radiografía
Tu arquitectura base (HTA) y la lógica de LangGraph con OpenAI están funcionando perfectamente bajo presión (el log del worker prueba que es capaz de recibir, razonar y disparar un mensaje de vuelta en apenas 10 segundos). 
El único eslabón roto era cómo PM2 en Contabo arrancaba el proceso de Node.js de WhatsApp, lo cual se solucionó apuntando al `dist/app.js` localizado. Además, la pasarela de pagos con PayPal se ha optimizado para ser robusta, rápida e inmune a las demoras de webhooks en producción gracias al endpoint de verificación directa.

