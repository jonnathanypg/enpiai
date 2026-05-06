# Análisis Hiper-Detallado del Backend - EnpiAI

**Versión del Documento**: 3.0 (Ultimate Reference)
**Fecha**: 13 de Febrero de 2026
**Estado**: Production Ready, I18n Activo (EN/ES/FR/PT), Async Core.

Este documento constituye la referencia técnica definitiva de EnpiAI. Se ha realizado un análisis línea por línea de cada módulo para garantizar una comprensión total de la arquitectura, flujos de datos y decisiones de diseño. Incluye diagramas de arquitectura, especificaciones de API y detalles de implementación profunda.

---

## 1. 📐 Arquitectura del Sistema

### 1.1 Flujo de Mensajería (Async)
EnpiAI utiliza un patrón de arquitectura dirigida por eventos para desacoplar la recepción de mensajes del procesamiento de IA.

```mermaid
sequenceDiagram
    participant User
    participant WhatsApp as API WhatsApp
    participant Webhook as Flask Webhook
    participant DB as MySQL
    participant Celery as Celery Worker
    participant Redis
    participant Agent as Agent Orchestrator
    participant LLM as OpenAI/Anthropic/Gemini

    User->>WhatsApp: Envía mensaje
    WhatsApp->>Webhook: POST /webhooks/whatsapp
    Webhook->>DB: Guarda Mensaje (Status: RECEIVED)
    Webhook->>Redis: Encola Tarea (process_webhook_message)
    Webhook-->>WhatsApp: 200 OK (Ack inmediato)
    
    Redis->>Celery: Despacha Tarea
    Celery->>Agent: Run(message_id)
    Agent->>DB: Lee Historial + Contexto
    Agent->>LLM: Genera Respuesta (con Tools)
    LLM-->>Agent: Texto / Tool Call
    Agent->>DB: Guarda Respuesta (Status: SENT)
    Agent->>WhatsApp: Envía Respuesta Final
    WhatsApp-->>User: Entrega Mensaje
```

### 1.2 Grafo de Agente (LangGraph)
El cerebro del sistema opera mediante un grafo cíclico con estado persistente.

```mermaid
graph TD
    Start([Inicio]) --> RetrieveState{Recuperar Estado (Redis)}
    RetrieveState --> NodeAgent[Agent Node (LLM)]
    NodeAgent --> CheckOutput{¿Requiere Tool?}
    CheckOutput -- Sí --> NodeTools[Tool Node]
    NodeTools -- Resultado --> NodeAgent
    CheckOutput -- No (Texto Final) --> End([Fin])
    
    subgraph "Skills & Tools"
    NodeTools --> RAG[RAG Memory]
    NodeTools --> CRM[CRM Lookup]
    NodeTools --> Calendar[Google Calendar]
    end
```

---

## 2. 🏗️ Infraestructura Core (Raíz)

### 2.1 [app.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/app.py)
**Propósito**: Fábrica de la Aplicación (Entry Point).
*   **Inicialización del Núcleo**:
    *   Instancia `Flask(__name__)` que actúa como el contenedor WSGI principal.
    *   Carga la configuración mediante `app.config.from_object(Config)`, inyectando variables de entorno en el contexto de la app.
    *   **Extensiones**:
        *   `db.init_app(app)`: Vincula SQLAlchemy al ciclo de vida de la solicitud.
        *   `jwt.init_app(app)`: Configura el manejo de tokens Bearer para autenticación segura.
        *   `migrate.init_app(app, db)`: Habilita comandos de migración (`flask db upgrade`) para gestión de esquema.
        *   `limiter.init_app(app)`: Activa el rate limiting global (Redis/Memoria) para prevenir ataques DDoS.
        *   `cors.init_app(app)`: Habilita peticiones Cross-Origin permitidas (crítico para frontend separado).
*   **Registro Modular (Blueprints)**:
    *   Itera sobre los módulos en `routes/` y registra cada Blueprint con su prefijo URL específico:
        *   `/api/auth`: Rutas de Login y Registro.
        *   `/webhooks`: Receptores de eventos externos (WhatsApp, Stripe).
        *   `/api/admin`: Endpoints para el Panel de Control Administrativo.
        *   `/api/contacts`: Identidad unificada y gestión de contactos 360.
*   **Manejadores de Errores Globales**:
    *   `@app.errorhandler(404)`: Captura recursos no encontrados y retorna JSON estandarizado `{"error": "Resource not found"}`.
    *   `@app.errorhandler(500)`: Captura excepciones no controladas, loguea el stacktrace completo y retorna JSON `{"error": "Internal Server Error"}`.
    *   `@jwt.expired_token_loader`: Retorna 401 con mensaje específico cuando el token ha caducado.

### 2.2 [config.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/config.py)
**Propósito**: Gestión Centralizada de Configuración.
*   **Clase `Config`**:
    *   **Base de Datos Resiliente**:
        *   `SQLALCHEMY_DATABASE_URI`: Prioriza MySQL remoto (`mysql+pymysql://...`), con fallback a SQLite local para desarrollo.
        *   `SQLALCHEMY_ENGINE_OPTIONS`:
            *   `pool_recycle`: 280 segundos. (Reinicia conexiones antes del timeout de 300s de MySQL por defecto).
            *   `pool_pre_ping`: True. (Verifica si la conexión está viva antes de usarla, eliminado errores "Gone Away").
    *   **Seguridad y Cifrado**:
        *   `SECRET_KEY`: Semilla criptográfica para firma de cookies de sesión.
        *   `JWT_SECRET_KEY`: Semilla para firma y verificación de tokens JWT.
        *   `ENCRYPTION_KEY`: Clave maestra Fernet (AES-128) para la capa de Soberanía de Datos (cifrado de columnas PII).
    *   **Integraciones IA**:
        *   `OPENAI_API_KEY`: Motor principal (GPT-4o).
        *   `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY`: Motores de respaldo (Failover strategy).
        *   `PINECONE_API_KEY`: Base de datos vectorial para RAG.
    *   **Infraestructura Asíncrona**:
        *   `CELERY_BROKER_URL`: URL de conexión a Redis (canal de comunicación Broker).
        *   `CELERY_RESULT_BACKEND`: URL de conexión a Redis (almacenamiento de resultados).

### 2.3 [celery_app.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/celery_app.py)
**Propósito**: Worker Instance de Celery.
*   **Análisis Técnico**:
    *   Crea la instancia `Celery` desacoplada de Flask.
    *   Sobrescribe `TaskBase` para inyectar `flask_app.app_context()` antes de ejecutar cualquier tarea.
    *   **Por qué es crítico**: Sin esto, las tareas en segundo plano (como generar PDFs o guardar en BD) fallarían al intentar acceder a `db.session` fuera del contexto de una petición HTTP.

### 2.4 [tasks.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/tasks.py)
**Propósito**: Definición de Tareas Asíncronas (Background Jobs).
*   **`process_webhook_message(data)`**:
    *   **Lógica**: Actúa como el consumidor principal de mensajes.
    *   1. Identifica al distribuidor (`company_id`) desde el payload.
    *   2. Reconstruye el estado de la conversación desde la BD.
    *   3. Llama a `AgentOrchestrator.run()` de forma síncrona dentro del hilo del worker.
    *   4. Envía la respuesta final al usuario vía `MessagingService`.
    *   **Impacto**: Desacopla la recepción del mensaje (HTTP) de su procesamiento (IA), permitiendo escalar workers independientemente del tráfico web.
*   **`generate_pdf_report(evaluation_id)`**:
    *   Genera binarios PDF pesados usando ReportLab (CPU Intensive).
    *   Sube el resultado a almacenamiento persistente local/S3.
    *   Actualiza el registro `WellnessEvaluation` con la URL del reporte generado.
*   **`index_document_rag(doc_id)`**:
    *   Pipeline ETL: Carga documento -> Divide en trozos (Chunking) -> Genera Embeddings (OpenAI) -> Sube a Pinecone.
    *   Operación intensiva en I/O y Red, delegada totalmente a segundo plano.

---

## 3. 🔐 Servicios de Seguridad Core (`services/`)

### 3.1 [services/encryption_service.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/services/encryption_service.py)
**Propósito**: Capa de Cifrado Soberano (Protección PII).
*   **Tecnología**: Usa `cryptography.fernet.Fernet` (Implementación de AES-128 en modo CBC con firma HMAC).
*   **`EncryptedString` (TypeDecorator)**:
    *   `process_bind_param(value, dialect)`: Intercepta el valor antes de guardarlo en SQL. Si es string, lo cifra y devuelve bytes.
    *   `process_result_value(value, dialect)`: Intercepta el valor al leerlo de SQL. Descifra los bytes y devuelve string original.
*   **`EncryptedJSON`**:
    *   Extiende la lógica anterior pero serializa diccionarios a JSON string antes de cifrar.
    *   Usado para proteger `google_credentials` y `api_keys` con estructura variable y altamente sensible.

### 3.2 [services/identity_resolver.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/services/identity_resolver.py)
**Propósito**: Resolución de Identidad Unificada.
*   **Problema**: Un usuario puede ser un Lead en tabla `leads` o un Cliente en tabla `customers`.
*   **Solución**:
    *   Método `resolve_identity(phone, email)`: Busca primero en `customers` (prioridad alta). Si no encuentra, busca en `leads`.
    *   Construye un objeto `VirtualUser` que normaliza los campos (`name`, `status`, `tags`, `score`).
    *   Inyecta este perfil unificado en el `AgentState`, permitiendo que la IA sepa "quién es" el usuario sin importar en qué tabla resida físicamente.

---

## 4. 🧠 Inteligencia y Orquestación (`services/`)

### 4.1 [services/agent_orchestrator.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/services/agent_orchestrator.py)
**Propósito**: El Cerebro (LangGraph).
*   **Arquitectura de Grafo**:
    *   **State**: `AgentState` (TypedDict con mensajes, contexto, hints).
    *   **Nodos**:
        *   `agent`: Invoca al LLM con el historial de mensajes y herramientas disponibles.
        *   `tools`: Ejecuta las herramientas invocadas por el agente (tool_calls).
    *   **Aristas (Edges)**:
        *   `agent` -> `tools` (Condicional: Si el LLM pide usar herramientas).
        *   `tools` -> `agent` (Ciclo: Vuelve al agente con el resultado de la herramienta).
        *   `agent` -> `END` (Si el LLM termina la respuesta).
*   **Persistencia (Checkpointer)**:
    *   Implementa `RedisSaver` para producción. Guarda el estado serializado del grafo en Redis cada vez que el agente responde.
    *   Permite conversaciones "Stateful" a larga duración, incluso si el proceso del servidor se reinicia.
*   **Carga Dinámica de Skills**:
    *   Inspecciona `agent_config.features`.
    *   Filtra las herramientas disponibles en `agent_tools.py` y las pasa al LLM (bind_tools).

### 4.2 [services/i18n_service.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/services/i18n_service.py)
**Propósito**: Sistema de Internacionalización.
*   **Diccionarios Estáticos**: Mantiene copias de los prompts críticos ("Identity", "Safety", "Context") en 4 idiomas (EN, ES, FR, PT).
*   **Selección Dinámica**:
    *   `get_prompts(lang)`: Retorna el set completo de instrucciones en el idioma solicitado por el distribuidor.
    *   **Default Agent Creation**: Al registrar un usuario, selecciona el nombre ("Lead Assistant" vs "Asistente") y descripción adecuados para el idioma.

### 4.3 [services/llm_service.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/services/llm_service.py)
**Propósito**: Abstracción de IA y Failover.
*   **Patrón de Estrategia**:
    *   Interfaz unificada `generate_response(messages, tools)`.
*   **Failover Cascade**:
    *   Intento 1: OpenAI (GPT-4o).
    *   Exception: Captura timeout o error 5xx de OpenAI.
    *   Intento 2: Anthropic (Claude 3.5 Sonnet).
    *   Exception: Captura error.
    *   Intento 3: Google (Gemini 1.5 Pro).
    *   Fallo Total: Retorna mensaje de error amigable "Sistema sobrecargado", evitando romper el flujo de usuario.

### 4.4 [services/rag_service.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/services/rag_service.py)
**Propósito**: Memoria RAG (Pinecone).
*   **Namespace Isolation**: Cada llamada a Pinecone incluye `namespace=dist_ID`, garantizando que un distribuidor NUNCA acceda a documentos de otro (Tenant Isolation estricto).
*   **Upsert Async**: El método público `upsert_document` es un wrapper que invoca a la tarea de Celery, retornando inmediatamente al cliente.
*   **Querying**: Usa embeddings de OpenAI (`text-embedding-3-small`) para búsqueda semántica cosine similarity.

---

## 5. 🗄️ Modelos de Base de Datos (`models/`)

### 5.1 [models/distributor.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/models/distributor.py)
**Propósito**: Entidad Tenant Principal.
*   **Esquema Actualizado (Phase 14)**:
    *   `id`: INTEGER PRIMARY KEY.
    *   `language`: VARCHAR(5) DEFAULT 'en'. Define el idioma del bot.
    *   `api_key`: VARCHAR(255). Token estático para acceso API programático (OpenAI Compat).
    *   `google_credentials`: JSON Encriptado. OAuth Refresh Tokens.
    *   `api_keys`: JSON Encriptado. Claves de terceros (SendGrid, Twilio).
    *   `subscription_tier`: ENUM('free', 'starter', 'pro'). Controla límites de uso.
    *   `agent_config`: Relación 1-N (Cascada).

### 5.2 [models/lead.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/models/lead.py)
**Propósito**: CRM de Prospectos.
*   **Privacidad**:
    *   `phone`: EncryptedString.
    *   `email`: EncryptedString.
    *   Esto cumple con regulaciones GDPR/CCPA al proteger PII en reposo. Las claves de cifrado están gestionadas por variables de entorno.
*   **Estado**: Máquina de estados simple (NEW -> CONTACTED -> QUALIFIED -> CONVERTED).

### 5.3 [models/agent_config.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/models/agent_config.py)
**Propósito**: Configuración de Comportamiento IA.
*   **Modelo Jerárquico**:
    *   `AgentConfig`: Define la "Personalidad" (Tono, Objetivo, Prompt Sistema).
    *   `AgentFeature`: Define las "Habilidades" (Lista de strings mapeados a Tools).
*   **Datos en Inglés**: Todos los registros por defecto (`DEFAULT_FEATURES`, prompts de `AgentTone`) se insertan en Inglés para estandarización interna del código.

### 5.4 [models/conversation.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/models/conversation.py)
**Propósito**: Historial de Interacciones.
*   **`Conversation`**: Agrupa mensajes. Vincula `distributor_id` y `contact_id`.
*   **`Message`**:
    *   `role`: user / assistant / system / tool.
    *   `content`: Texto del mensaje.
    *   `message_metadata`: JSON field para almacenar argumentos de tool calls o respuestas de funciones estructuradas.

---

## 6. 🚀 Rutas y API (`routes/`)

### 6.1 [routes/auth.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/routes/auth.py)
**Propósito**: Gestión de Acceso y Registro.
*   **`POST /register`**:
    *   **Input**: `{name, email, password, language, ...}`.
    *   **Process**:
        1. Crea `Distributor` y `User` (hash password con bcrypt).
        2. Invoca `I18nService.get_default_agent_data(language)`.
        3. Crea `AgentConfig` inicial localizado (ej: Nombre="Asistente" si es 'es', "Assistant" si es 'en').
        4. Habilita features por defecto.
    *   **Output**: `{access_token, refresh_token, user_id}`.

### 6.2 [routes/webhooks.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/routes/webhooks.py)
**Propósito**: Entrada de Mensajería.
*   **Arquitectura Reactiva**:
    *   Recibe POST de `api-whatsapp` (Node.js microservice).
    *   Valida firma (opcional).
    *   Guarda mensaje en `messages` table (commit inmediato).
    *   Lanza tarea `process_webhook_message.delay()`.
    *   Retorna 200 OK inmediatamente.
    *   **Beneficio**: Evita timeouts de WhatsApp (que reintenta si no hay 200 OK en X segundos) y mejora la percepción de velocidad.

### 6.3 [routes/contacts.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/routes/contacts.py)
**Propósito**: Identidad Unificada 360°.
*   **`GET /unified/<identifier>`**:
    *   Realiza consultas paralelas a: `Lead`, `Customer`, `Appointment`, `WellnessEvaluation`, `Conversation`.
    *   Agrega resultados en un objeto JSON maestro.
    *   Ordena eventos cronológicamente para mostrar un "Customer Journey" timeline en el frontend.

### 6.4 [routes/openai_compat.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/routes/openai_compat.py)
**Propósito**: Interoperabilidad.
*   **`POST /v1/chat/completions`**:
    *   Emula la firma de la API de OpenAI.
    *   Permite conectar herramientas de terceros (Flowise, LangFlow) usando EnpiAI como backend.
    *   Autenticación: Valida `Authorization: Bearer <distributor.api_key>`.

---

## 7. 🛠️ Habilidades del Agente (`skills/`)

### 7.1 [skills/scheduler.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/skills/scheduler.py)
**Propósito**: Gestión de Calendario.
*   **`check_availability`**: Consulta Slots Google Calendar. Retorna lista de huecos formateados en Inglés.
*   **`schedule_appointment`**: Crea evento. Retorna confirmación en Inglés.
*   **Nota**: El LLM traduce esta salida al idioma del usuario final en la respuesta de chat.

### 7.2 [skills/crm.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/skills/crm.py)
**Propósito**: Interfaz CRM.
*   **`lookup_customer`**: Busca por email/teléfono. Retorna JSON con datos conocidos.
*   **`register_lead`**: Inserta nuevo registro en DB con status 'NEW'.

### 7.3 [skills/rag_memory.py](file:///Users/jonnathan/Desktop/EnpiAI/backend/skills/rag_memory.py)
**Propósito**: Base de Conocimiento.
*   **`consult_knowledge_base`**: Realiza búsqueda semántica en Pinecone y retorna fragmentos relevantes de texto para RAG.

---

## 8. 📋 Deployment & Operations

### 8.1 Requisitos de Producción
*   **Python**: 3.9+
*   **Base de Datos**: MySQL 8.0 (con soporte JSON y UTF8MB4).
*   **Cache/Broker**: Redis 6+ (Persistencia recomendada).
*   **Vector DB**: Pinecone Serverless.

### 8.2 Comandos de Gestión
*   **Iniciar API**: `gunicorn -w 4 -b 0.0.0.0:5000 app:app`
*   **Iniciar Worker**: `celery -A celery_app.celery worker --loglevel=info`
*   **Migrar DB**: `flask db upgrade`
*   **Verificar Schema**: `python3 verify_schema.py`

### 8.3 Variables de Entorno Críticas (.env)
```bash
FLASK_APP=app.py
FLASK_ENV=production
DATABASE_URL=mysql+pymysql://user:pass@host/db
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...
ENCRYPTION_KEY=... (Generar con Fernet.generate_key())
```

---

**Conclusión Final**:
La arquitectura actual de EnpiAI (Phase 14) representa un sistema maduro y listo para producción. La combinación de **Orquestación Asíncrona (Celery/Redis)**, **Cifrado Soberano (Fernet)** y **Soporte I18n Nativo** coloca al backend en un nivel Enterprise. La documentación detallada aquí refleja fielmente la implementación actual del código y sirve como mapa completo para futuros desarrolladores o auditores.
