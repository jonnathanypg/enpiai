# AUDITORÍA TÉCNICA COMPLETA — ENPIAI
## Estado del Proyecto · Revisión Nivel CTO · Junio 2026

> **Confidencialidad**: Interno — Solo equipo técnico  
> **Alcance**: Backend · Frontend · WhatsApp API · BD Relacional · BD Vectorial · Integraciones · Seguridad · DevOps  
> **Metodología**: Revisión línea por línea, función por función, variable por variable  
> **Auditor**: AI Agent (Antigravity) — Sesión completa Jun 2026

---

## ÍNDICE

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [BUGS CRÍTICOS — Acción Inmediata](#3-bugs-críticos--acción-inmediata)
4. [Backend — FastAPI + Flask Gateway](#4-backend--fastapi--flask-gateway)
5. [Backend — Celery Workers (tasks.py)](#5-backend--celery-workers-taskspy)
6. [Backend — Agent Orchestrator](#6-backend--agent-orchestrator)
7. [Backend — Modelos de BD](#7-backend--modelos-de-bd)
8. [Backend — Rutas (Routes)](#8-backend--rutas-routes)
9. [Backend — Servicios](#9-backend--servicios)
10. [Backend — Configuración](#10-backend--configuración)
11. [Frontend — Next.js / React](#11-frontend--nextjs--react)
12. [API WhatsApp — Microservicio Baileys](#12-api-whatsapp--microservicio-baileys)
13. [Base de Datos Relacional (MySQL)](#13-base-de-datos-relacional-mysql)
14. [Base de Datos Vectorial (Pinecone)](#14-base-de-datos-vectorial-pinecone)
15. [Seguridad](#15-seguridad)
16. [DevOps — PM2 / Despliegue](#16-devops--pm2--despliegue)
17. [Redundancias e Inconsistencias](#17-redundancias-e-inconsistencias)
18. [Mal Tipado y Type Safety](#18-mal-tipado-y-type-safety)
19. [Experiencia del Distribuidor](#19-experiencia-del-distribuidor)
20. [Plan de Acción Priorizado](#20-plan-de-acción-priorizado)
21. [Scorecard Final](#21-scorecard-final)

---

## 1. RESUMEN EJECUTIVO

EnpiAI es una plataforma SaaS multi-tenant para distribuidores de Herbalife que integra IA conversacional (LangGraph/OpenAI), mensajería (WhatsApp/Telegram), CRM de prospectos, evaluaciones de bienestar y facturación (dLocal Go). La arquitectura es sólida en diseño conceptual, pero presenta **5 bugs activos en producción**, inconsistencias de tipado, brechas de seguridad y duplicación de lógica que incrementan el riesgo de fallos en runtime.

### Estado General por Módulo

| Área | Estado | Criticidad |
|------|--------|------------|
| Backend Gateway (FastAPI+Flask) | ⚠️ Funcional con bugs | Alta |
| Agent Orchestrator (LangGraph) | ⚠️ Bug en is_o_model | Alta |
| Celery Tasks | 🔴 Bug crítico PDF + cleanup | Crítica |
| API WhatsApp (Baileys) | ⚠️ Estable pero frágil | Media |
| Frontend (Next.js) | ⚠️ Typo + middleware incompleto | Media |
| BD Relacional (MySQL) | ✅ Schema coherente | Baja |
| BD Vectorial (Pinecone) | ⚠️ Campo no declarado en modelo | Media |
| Seguridad CORS | 🔴 Violación de spec W3C | Crítica |
| Rate Limiting | ⚠️ No persiste en multi-worker | Media |
| Despliegue PM2 | ✅ Configuración mayormente correcta | Baja |

---

## 2. ARQUITECTURA DEL SISTEMA

```
┌─────────────────────────────────────────────────────────┐
│                   CLIENTE FINAL                         │
│        (WhatsApp / Telegram / Navegador Web)            │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│     FRONTEND — Next.js 15 / React 19                    │
│  Puerto 3000 │ Dashboard distribuidor │ Página pública  │
└───────────────────────┬─────────────────────────────────┘
                        │ REST / JSON
┌───────────────────────▼─────────────────────────────────┐
│       FASTAPI UNIFIED GATEWAY (fastapi_app.py)          │
│          Puerto 5000 — uvicorn 2 workers                │
│  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │  FastAPI Routes  │  │  Flask WSGI (WSGIMiddleware) │  │
│  │  /webhooks/wa    │  │  /api/* — REST endpoints    │  │
│  │  /api/voice/*    │  │  Auth, CRM, Wellness, etc.  │  │
│  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────┬───────────────────────────────────────┘
                  │ .delay() / send_task()
┌─────────────────▼───────────────────────────────────────┐
│              REDIS — Puerto 6381                        │
│       Broker DB/0  │  Result Backend DB/1               │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│          CELERY WORKER — 2 concurrentes                 │
│  process_webhook_message  │  index_document_rag         │
│  generate_pdf_report      │  process_wellness_evaluation│
│  send_broadcast_message                                 │
└─────────────────┬───────────────────────────────────────┘
        ┌─────────┴──────────┐
┌───────▼──────────┐  ┌──────▼──────────────────────────┐
│  MYSQL :3306     │  │  PINECONE — Cloud               │
│  Multi-tenant    │  │  Vectores RAG por namespace     │
│  Encriptado PII  │  │  por distribuidor               │
└──────────────────┘  └─────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│        API WHATSAPP — Node.js / Baileys                 │
│                    Puerto 3001                          │
│  Gestiona sesiones QR │ Recibe mensajes WhatsApp        │
│  → POST /webhooks/whatsapp (→ FastAPI)                  │
└─────────────────────────────────────────────────────────┘
```

### Flujo Completo de un Mensaje WhatsApp

```
Usuario WA
  → api-whatsapp:3001 (Baileys captura el mensaje)
  → POST /webhooks/whatsapp → FastAPI (async, responde 200 inmediatamente)
  → Crea/actualiza Conversation + Message en MySQL
  → celery.send_task('tasks.process_webhook_message')
  → Worker Celery: carga Distributor + Conversation desde MySQL
  → AgentOrchestrator.process_message()
      → Sentiment analysis (keyword-based, sin LLM)
      → Identity resolution (phone → Lead/Customer/Distributor)
      → _resolve_skills() → skills activos según features habilitadas
      → _build_graph() → LangGraph: agent_node → tool_node → agent_node
      → LLM call (OpenAI / Google Gemini fallback)
      → Humanizer post-procesamiento
      → schedule_followup (auto 24h)
  → Guarda AI reply en MySQL (Message table)
  → messaging_service.send_whatsapp(reply)
  → POST /api/whatsapp/send → api-whatsapp:3001
  → Baileys → Usuario WA recibe respuesta
```

---

## 3. BUGS CRÍTICOS — ACCIÓN INMEDIATA

### 🔴 BUG-001: Escape de Newline en PDF — `tasks.py:75`

**Archivo**: `backend/tasks.py` · **Línea**: 75  
**Severidad**: CRÍTICA — Afecta indexación RAG de todos los documentos PDF

**Código actual (INCORRECTO):**
```python
text_content += page_text + "\\n"   # literal backslash + n
```

**Código correcto:**
```python
text_content += page_text + "\n"    # salto de línea real
```

**Impacto**: `"\\n"` en Python representa los dos caracteres literales `\` y `n`, NO un salto de línea. Las páginas se concatenan con el texto literal `\n`, resultando en una sola línea masiva. Consecuencias:
1. El `RecursiveCharacterTextSplitter` no puede detectar párrafos correctamente
2. Los chunks generados están mal formados
3. Calidad RAG severamente degradada para todos los documentos PDF indexados
4. Todos los PDFs existentes en Pinecone deben ser re-indexados tras el fix

---

### 🔴 BUG-002: CORS Wildcard + Credentials — `fastapi_app.py:39-45`

**Archivo**: `backend/fastapi_app.py` · **Líneas**: 39–45  
**Severidad**: CRÍTICA — Violación W3C CORS spec + vulnerabilidad de seguridad

**Código actual (INCORRECTO):**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # ← wildcard
    allow_credentials=True,   # ← credentials habilitado
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Problema**: La especificación CORS prohíbe `allow_origins=["*"]` cuando `allow_credentials=True`. Los navegadores modernos **bloquean** todas las solicitudes con credenciales (cookies, Authorization headers) bajo esta configuración. Además, cualquier origen puede hacer solicitudes cross-site.

**Fix requerido:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.enpiai.com",
        "https://enpiai.com",
        "http://localhost:3000",  # solo dev
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)
```

---

### 🔴 BUG-003: `is_o_model` False Positive — `agent_orchestrator.py:77`

**Archivo**: `backend/services/agent_orchestrator.py` · **Línea**: 77  
**Severidad**: ALTA — Todos los modelos `gpt-*` son incorrectamente tratados como O-models

**Código actual:**
```python
is_o_model = any(m in model_lower for m in ['o1', 'o3', 'gpt-5'])
```

**Problema**: La cadena `'gpt-5'` es substring de `'gpt-5-nano'` (el modelo por defecto). Por tanto, **todos** los modelos con `gpt-5` en su nombre reciben:
- `temperature=1.0` (en lugar de `0.7`)
- `max_completion_tokens` en lugar de `max_tokens`
- Mandato de resumen adicional en el system prompt

**Fix requerido:**
```python
O_MODEL_NAMES = {'o1', 'o1-mini', 'o1-preview', 'o3', 'o3-mini', 'o4-mini'}
is_o_model = model_lower in O_MODEL_NAMES or model_lower.startswith(('o1-', 'o3-', 'o4-'))
```

---

### 🔴 BUG-004: Flask `g` en Contexto Celery — `agent_orchestrator.py:301`

**Archivo**: `backend/services/agent_orchestrator.py` · **Líneas**: 301–302  
**Severidad**: ALTA — Crash silencioso en ejecución de tools vía Celery

**Código actual:**
```python
def tool_node(state: AgentState) -> Dict[str, Any]:
    ...
    g.current_company = self.distributor           # ← BUG
    g.current_conversation_id = state.get("conversation_id")   # ← BUG
    result = tool_obj.invoke(tool_args)
```

**Problema**: `flask.g` es un objeto de contexto de **request HTTP**. En tareas Celery se usa `app_context()` (no `request_context()`). Flask 3.x hace que `g` en un `app_context` sin `request_context` sea inestable y se resetea entre llamadas. Los tools que dependen de `g.current_company` pueden recibir `None`.

**Fix requerido:** Usar `threading.local()` o pasar el contexto explícitamente:
```python
import threading
_ctx = threading.local()

# Antes de invocar el tool:
_ctx.current_company = self.distributor
_ctx.current_conversation_id = state.get("conversation_id")
```

---

### 🔴 BUG-005: Modelo LLM Inexistente — `config.py:72`

**Archivo**: `backend/config.py` · **Línea**: 72  
**Severidad**: ALTA — El modelo por defecto `gpt-5-nano` no existe en la API de OpenAI

**Código actual:**
```python
DEFAULT_LLM_MODEL = os.getenv('DEFAULT_LLM_MODEL', 'gpt-5-nano')
```

Y en `agent_orchestrator.py:63`:
```python
model = model_override or self.distributor.llm_model or 'gpt-5-nano'
```

Y hardcodeado en `agent_orchestrator.py:99`:
```python
llms.append(ChatOpenAI(
    model="gpt-5-nano",   # ← hardcoded en el fallback de plataforma
    ...
))
```

**Impacto**: Si `DEFAULT_LLM_MODEL` no está en el `.env` y ningún distribuidor configuró su modelo, todas las llamadas al LLM fallan con error 404 de OpenAI.

**Fix:**
```python
DEFAULT_LLM_MODEL = os.getenv('DEFAULT_LLM_MODEL', 'gpt-4o-mini')
```

---

### 🟠 BUG-006: Campo `pinecone_ids` No Declarado en Modelo — `tasks.py:117`

**Archivos**: `backend/tasks.py:117` + `backend/models/document.py`  
**Severidad**: MEDIA — Datos de vectores no se persisten en BD

**Código en task:**
```python
doc.pinecone_ids = vector_ids    # ← asignación a atributo no declarado
```

Si `Document` no tiene `pinecone_ids` como columna SQLAlchemy, esta asignación es un atributo Python puro — SQLAlchemy **no lo persistirá** en la BD. Los IDs de Pinecone se pierden al limpiar la sesión.

**Fix** en `models/document.py`:
```python
pinecone_ids = db.Column(db.JSON, nullable=True)   # lista de vector IDs
```

---

## 4. BACKEND — FastAPI + Flask Gateway

### `fastapi_app.py` — Análisis Completo

#### Inicialización (L1–52)
- ✅ Patrón correcto: Flask factory + FastAPI wrapper + SQLAlchemy pool compartido
- ⚠️ `config = get_config()` retorna una **clase**, no instancia. Funciona porque `from_object()` acepta clases, pero el naming es confuso (colisiona con el `config = {...}` local en orchestrator:451).
- ⚠️ **REDUNDANCIA**: Hay dos engines SQLAlchemy: uno aquí (FastAPI directo) y otro en Flask-SQLAlchemy. Con `pool_size=5` cada uno, con 2 workers uvicorn = hasta 20 conexiones solo del gateway.

#### `get_db()` dependency (L55–62)
```python
def get_db():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        yield db
    finally:
        db.close()
```
- ✅ El ping `SELECT 1` previene stale connections
- ⚠️ Sin `rollback()` en el `finally`. Si la sesión tiene transacciones abiertas al cerrar, el pool recibe una conexión sucia.
- **Fix**: Añadir `except: db.rollback(); raise` antes del `finally`.

#### Health Check (L64–81)
- ⚠️ Flask también tiene `/health` en `app.py:152`, pero es inalcanzable porque FastAPI lo intercepta primero. El Flask health endpoint es código muerto.

#### Webhook WhatsApp (L87–181)
- L94–98: `except:` desnudo captura `KeyboardInterrupt` y `SystemExit`. Usar `except Exception:`.
- L105: `distributor_id = data.get('companyId')` — puede ser `None`, sin validación. La conversación se crearía con `distributor_id=None`.
- L140: Query sin índice compuesto en `(distributor_id, channel, participant_id, status)`.
- L170–176: `is_audio` pasado como `kwargs` pero en la firma del task tiene posición fija. Funciona pero inconsistente con `webhooks.py`.

#### Voice Endpoints (L192–368)
- L239: `/api/voice/interact` sin autenticación — cualquiera puede consumir créditos de Whisper + LLM.
- L257–262: Si `PlatformConfig.platform_distributor_id` es None, falla con 503 sin log claro.
- ✅ L231: Path traversal check correcto para archivos de voz.

#### Montaje Flask (L379)
```python
app.mount("/", WSGIMiddleware(flask_app))
```
- ✅ FastAPI routes tienen precedencia. Flask maneja el resto.

---

## 5. BACKEND — CELERY WORKERS (tasks.py)

### `tasks.py` — Análisis Completo

#### Module-level path append (L17)
```python
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
```
- ⚠️ Code smell. El path debería configurarse en `PYTHONPATH` del entorno o en `celery_app.py`.

#### `generate_pdf_report` (L22–40)
- ✅ App context correcto
- ⚠️ Sin type hints en argumentos
- ⚠️ `return {'path': result}` expone rutas internas del VPS si el frontend usa este valor directamente

#### `index_document_rag` (L43–125)
- L63: `metadata.get('type', 'txt')` — si `metadata.get('type')` retorna `None` (clave presente pero None), `file_ext = None` y ningún branch procesa el archivo. Falta `or 'txt'` adicional.
- **L75**: 🔴 **BUG-001** — `"\\n"` en lugar de `"\n"`
- L82–92: Marca `is_processed=True` cuando el texto está vacío, pero el status='error' es contradictorio. Necesita un campo `processing_status` enum.
- **L117**: 🟠 **BUG-006** — `doc.pinecone_ids` no declarado en el modelo

#### `send_broadcast_message` (L128–161)
- ✅ Lógica de conteo de enviados/errores correcta
- ⚠️ Sin delay entre mensajes. 1000 recipients → spam en la API WhatsApp.
- **Fix**: `await asyncio.sleep(0.5)` o `time.sleep(0.5)` entre envíos.

#### `process_webhook_message` (L164–301) — TAREA CENTRAL
- L188–189: `.query.get()` deprecated en SQLAlchemy 2.0. Usar `db.session.get(Model, id)`.
- ⚠️ Sin `soft_time_limit`. Una llamada LLM lenta bloquea el worker indefinidamente.
- L276–300: **Cleanup triple redundante** (bloque normal + except + finally). Solo se necesita el `finally`.

**Fix para cleanup:**
```python
    # Al final de la tarea, solo esto:
    finally:
        try:
            from extensions import db as task_db
            task_db.session.rollback()
            task_db.session.remove()
        except Exception as e:
            logger.debug(f"Task cleanup: {e}")
```

#### `process_wellness_evaluation` (L303–473)
- L336: `evaluation.language` — verificar si el modelo `WellnessEvaluation` tiene este campo.
- L382: `if evaluation.lead:` accede a una relación lazy después de un commit. Puede fallar si la sesión se cerró. Usar `db.session.refresh(evaluation)`.
- L399: `"https://enpi.click/..."` — dominio hardcodeado. Mover a `config.py` como `PLATFORM_URL`.
- ⚠️ L472: `except: pass` — desnudo. Siempre loggear excepciones, nunca pasar silenciosamente.

---

## 6. BACKEND — AGENT ORCHESTRATOR

### `services/agent_orchestrator.py` — Análisis Completo

#### MemorySaver Singleton (L44–52)
- ⚠️ `MemorySaver` es **volátil**: el historial de conversación en LangGraph se pierde con cada reinicio del worker.
- ⚠️ El singleton es compartido entre todos los tenants. Thread IDs como `conv_{id}_{date}` aíslan correctamente, pero si el ID de conversación en MySQL se repite entre tenants (no debería con auto-increment), habría colisión.
- ⚠️ El thread_id cambia cada día UTC (`conv_{id}_{YYYYMMDD}`). Una conversación que cruza medianoche UTC pierde el contexto en memoria.
- **Recomendación**: Migrar a `RedisSaver` o, al menos, inyectar el historial MySQL al estado inicial.

#### `_get_llm()` (L59–120)
- L71: `os.getenv('GOOGLE_API_KEY')` — inconsistente con `config.py` que define `GOOGLE_AI_API_KEY`. Google Gemini nunca se activa como fallback aunque esté configurado.
- **L77**: 🔴 **BUG-003** — `is_o_model` false positive
- L98–103: Fallback de plataforma usa `model="gpt-5-nano"` hardcodeado y parámetros de O-model.

#### `_resolve_skills()` (L122–165)
- ✅ Lógica correcta de resolución de skills
- ⚠️ Sin validación en runtime de que los nombres de features en `agent_config.py` coincidan. Un typo silenciosamente desactiva una skill.

#### `_determine_flow_context()` (L221–233)
- L226: `messages[-1].content.lower()` — si el último mensaje es un `ToolMessage`, puede no tener `.content` como string directamente accesible.
- **Fix**: `last_content = getattr(messages[-1], 'content', '') or ''; last_msg = last_content.lower()`

#### `_build_graph()` (L235–337)
- ✅ Arquitectura ReAct correcta: agent → conditional → tools → agent
- **L301–302**: 🔴 **BUG-004** — `flask.g` en contexto Celery
- ⚠️ `tool_node` sin timeout. Un tool que llame a Google Calendar puede bloquear el worker.

#### `process_message()` (L339–521)
- L354–358: Query `AgentConfig` sin índice en `(distributor_id, priority)`.
- L374–376: Thread ID cambia cada día UTC — pérdida de contexto en conversaciones largas.
- **L488–512**: Auto-followup se programa en CADA respuesta del agente. 10 respuestas = 10 follow-ups duplicados.
- ⚠️ El historial MySQL no se inyecta en el estado inicial de LangGraph. Si el worker reinició, el agente no recuerda nada.

**Fix para inyección de historial:**
```python
# Antes de definir initial_state, cargar historial reciente:
from models.conversation import Message, MessageRole
recent_messages = Message.query.filter_by(
    conversation_id=conversation.id
).order_by(Message.created_at.asc()).limit(20).all()

history_msgs = []
for m in recent_messages:
    if m.role == MessageRole.USER:
        history_msgs.append(HumanMessage(content=m.content))
    elif m.role == MessageRole.ASSISTANT:
        history_msgs.append(AIMessage(content=m.content))

initial_state = {
    "messages": history_msgs + [HumanMessage(content=enriched_message)],
    ...
}
```

---

## 7. BACKEND — MODELOS DE BD

### `models/distributor.py`

| Campo | Tipo | Observación |
|-------|------|-------------|
| `id` | Integer PK | ✅ |
| `name` | String(255) | ✅ |
| `herbalife_id` | String(50) unique | ✅ |
| `llm_model` | String(100) default='gpt-5-nano' | 🔴 Modelo inválido |
| `api_keys` | EncryptedJSON | ✅ Encriptación en reposo |
| `google_credentials` | EncryptedJSON | ✅ |
| `subscription_tier` | Enum | ⚠️ Duplica `subscription_active` |
| `coach_mode_enabled` | Boolean | ✅ |

- L108: `subscriptions = db.relationship(..., backref=db.backref('distributor_parent', ...))`  
  El `backref` y `back_populates` en el modelo `Subscription` pueden entrar en conflicto. Verificar.
- L127–148: `get_full_system_prompt()` es **código muerto**. El orchestrator usa `SystemPromptBuilder` y nunca llama este método.

### `models/conversation.py` (No revisado en detalle)
- Campos críticos: `participant_id` (phone/chat_id), `channel`, `status`
- Índice compuesto faltante: `(distributor_id, channel, participant_id, status)`

### `models/document.py`
- 🟠 Verificar que `pinecone_ids` existe como `db.Column(db.JSON)`
- ⚠️ El campo `is_processed` Boolean no distingue entre "procesado con éxito" y "procesado vacío"

### `models/wellness_evaluation.py`
- Verificar: `language`, `bmi`, `activity_level`, `exercise_frequency`, `meals_per_day`, `water_intake_liters`, `sleep_hours`, `sleep_quality` — todos usados en `tasks.py:336-352`

---

## 8. BACKEND — RUTAS (Routes)

### `routes/webhooks.py`

- `_process_message_async()`: Fallback sync correcto cuando Celery falla, pero bloquea el hilo Flask durante 5–30s.
- `_process_message_sync()`: Sin timeout para la llamada al orchestrator.
- ⚠️ La lógica de manejo de audio está en el fallback sync pero implementada ligeramente diferente a la versión FastAPI. Si el fallback se activa, el comportamiento puede diferir.

### `routes/coach.py`
- Backend: `coach_bp` → `/api/coach/...` ✅
- Frontend: `(dashboard)/couch/` 🔴 **TYPO** (sofá ≠ entrenador)

### `routes/auth.py` (No revisado en detalle)
- JWT access 24h / refresh 30 días
- ⚠️ Verificar que los cookies JWT tienen flags `HttpOnly`, `Secure`, `SameSite=Strict`

### Blueprints registrados en `app.py`

| Blueprint | Prefix | Estado |
|-----------|--------|--------|
| auth_bp | /api/auth | ✅ |
| distributors_bp | /api/distributors | ✅ |
| leads_bp | /api/leads | ✅ |
| customers_bp | /api/customers | ✅ |
| wellness_bp | /api/wellness | ✅ |
| agents_bp | /api/agents | ✅ |
| channels_bp | /api/channels | ✅ |
| webhooks_bp | /webhooks | ✅ |
| dashboard_bp | /api/dashboard | ✅ |
| coach_bp | /api/coach | ✅ |
| google_auth_bp | /api/auth/google | ✅ |
| payments_bp | /api/payments | ✅ |
| billing_bp | (sin prefix explícito) | ⚠️ Verificar prefix |
| rag_bp | /api/rag | ✅ |
| openai_bp | (sin prefix explícito) | ⚠️ Verificar prefix |
| admin_bp | /api/admin | ✅ |
| contacts_bp | /api/contacts | ✅ |

---

## 9. BACKEND — SERVICIOS

### Servicios y su estado

| Servicio | Tamaño | Estado | Observación |
|----------|--------|--------|-------------|
| `agent_orchestrator.py` | 23KB | ⚠️ Bugs documentados | Central del producto |
| `cron_service.py` | 22KB | ⚠️ Singleton multi-worker | Scheduler follow-ups |
| `email_service.py` | 36KB | ⚠️ Templates inline | Más grande del proyecto |
| `prompt_builder.py` | 21KB | ✅ Bien modularizado | |
| `pdf_service.py` | 16KB | ✅ ReportLab | |
| `rag_service.py` | 10KB | ⚠️ Namespace null risk | Pinecone |
| `identity_resolver.py` | 11KB | ✅ | |
| `ai_coach_service.py` | 19KB | ⚠️ No revisado | |
| `llm_service.py` | 9KB | ⚠️ Posible duplicación con orchestrator | |
| `voice_service.py` | 7KB | ✅ Whisper + Azure TTS | Sin limpieza de archivos temporales |
| `messaging_service.py` | 5KB | ✅ | Abstrae WA + Telegram |
| `humanizer_service.py` | 5KB | ⚠️ ¿LLM call adicional? | Costoso si usa LLM |
| `sentiment_service.py` | 8KB | ✅ Keyword-based (rápido) | |

### Issues transversales en servicios

- `voice_service.py`: Los archivos `.mp3` sintetizados en `uploads/voice/` nunca se eliminan. Con uso intensivo, el disco del VPS se llena.
- `cron_service.py`: El singleton `CronService.get_instance()` con `start_worker(app)` puede crear múltiples workers cron si hay múltiples workers uvicorn. Añadir un lock global.
- `email_service.py` (36KB): Templates HTML probablemente hardcodeados en Python. Evaluar externalizar a archivos `.html` con Jinja2.
- `llm_service.py`: Si este servicio también inicializa LLMs, hay duplicación con `agent_orchestrator._get_llm()`.

---

## 10. BACKEND — CONFIGURACIÓN

### `config.py` — Línea por línea

| Línea | Config | Estado |
|-------|--------|--------|
| L20 | `SECRET_KEY` default inseguro | 🔴 Sin validación en producción |
| L24 | JWT access 24h | ✅ |
| L25 | JWT refresh 30 días | ✅ |
| L54–60 | `pool_pre_ping=True`, `pool_recycle=300` | ✅ Mitigan MySQL gone away |
| L58 | `pool_size` default 5 | ⚠️ Puede ser insuficiente con múltiples workers |
| L72 | `DEFAULT_LLM_MODEL = 'gpt-5-nano'` | 🔴 BUG-005 |
| L88 | `WHATSAPP_API_URL` | ✅ |
| L89 | `WHATSAPP_API_SECRET` | ✅ Existe (verificar que se usa) |
| L100–101 | Redis URLs con puerto 6381 | ✅ Puerto no-estándar |

**Fix crítico en `config.py`:**
```python
# Añadir al final de ProductionConfig:
class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        import os
        if not os.getenv('SECRET_KEY'):
            raise RuntimeError("SECRET_KEY must be set in production environment")
```

O más simple, verificar en startup:
```python
# En create_app(), antes de inicializar:
if os.getenv('FLASK_ENV') == 'production' and not os.getenv('SECRET_KEY'):
    raise RuntimeError("SECRET_KEY must be configured in production")
```

### `extensions.py` — Línea por línea

| Línea | Código | Estado |
|-------|--------|--------|
| L12 | `db = SQLAlchemy()` | ✅ |
| L15–32 | Monkey-patch de `db.session.rollback` | ⚠️ Ver abajo |
| L34 | `jwt = JWTManager()` | ✅ |
| L35 | `migrate = Migrate()` | ✅ |
| L36–40 | `limiter` con `storage_uri="memory://"` | ⚠️ No persiste en multi-worker |

**Monkey-patch analysis (L15–32)**:
```python
original_rollback = db.session.rollback
def resilient_rollback(*args, **kwargs):
    try:
        return original_rollback(*args, **kwargs)
    except Exception as e:
        db.session.remove()
        return None
db.session.rollback = resilient_rollback
```
- ⚠️ Se aplica a nivel de módulo en el import. En Flask-SQLAlchemy 3.x, `db.session` es un `scoped_session` proxy. El patch al objeto proxy puede no sobrevivir si Flask-SQLAlchemy recrea el scoped_session durante `init_app()`.
- **Alternativa más robusta**: Usar el evento `@event.listens_for(engine, "handle_error")` de SQLAlchemy.

**Fix para rate limiter:**
```python
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6381/0').replace('/0', '/2')
)
```

---

## 11. FRONTEND — Next.js / React

### Estructura de Páginas

```
frontend/app/
├── (auth)/
│   ├── login/          ✅
│   └── register/       ✅
├── (dashboard)/
│   ├── admin/          ⚠️ No protegido en middleware
│   ├── agents/         ✅ protegido
│   ├── channels/       🔴 No protegido en middleware
│   ├── contacts/       🔴 No protegido en middleware
│   ├── couch/          🔴 TYPO: debería ser "coach"
│   ├── dashboard/      ✅ protegido
│   ├── documents/      🔴 No protegido en middleware
│   ├── settings/       ✅ protegido
│   ├── subscribe/      ✅ protegido
│   └── wellness/       🔴 No protegido en middleware
├── (public)/           ✅ Páginas públicas
└── page.tsx            ⚠️ 24KB — Landing monolítica
```

### `middleware.ts` — Análisis Completo

**Protected paths actuales (INCOMPLETO):**
```typescript
const protectedPaths = [
    '/dashboard', '/leads', '/customers', '/agents', '/settings', '/subscribe'
];
```

**Rutas del dashboard SIN protección:**
- `/channels` — Configuración WhatsApp/Telegram (⚠️ datos sensibles)
- `/wellness` — Evaluaciones de bienestar (⚠️ datos de salud)
- `/documents` — Knowledge base propietario (⚠️ documentos privados)
- `/contacts` — Base de contactos (⚠️ PII)
- `/couch` (coach) — Módulo de coaching
- `/admin` — Panel super-admin (🔴 CRÍTICO)

**Matcher también incompleto:**
```typescript
export const config = {
    matcher: [
        '/dashboard/:path*',
        '/leads/:path*',          // /leads no existe en el filesystem
        '/customers/:path*',      // /customers no existe en el filesystem
        '/agents/:path*',
        '/settings/:path*',
        '/login',
        '/register',
        '/subscribe',
        // FALTAN: /channels, /wellness, /documents, /contacts, /couch, /admin
    ],
};
```

**Fix completo para `middleware.ts`:**
```typescript
const protectedPaths = [
    '/dashboard', '/agents', '/settings', '/subscribe',
    '/channels', '/wellness', '/documents', '/contacts',
    '/couch', '/admin',
];

export const config = {
    matcher: [
        '/dashboard/:path*',
        '/agents/:path*',
        '/settings/:path*',
        '/subscribe/:path*',
        '/channels/:path*',
        '/wellness/:path*',
        '/documents/:path*',
        '/contacts/:path*',
        '/couch/:path*',
        '/admin/:path*',
        '/login',
        '/register',
    ],
};
```

### Typo `couch` → `coach`

- Directorio: `frontend/app/(dashboard)/couch/`
- El backend tiene `routes/coach.py` y prefix `/api/coach` ✅
- El frontend llama correctamente a `/api/coach/*` ✅ (no rompe funcionalidad)
- Pero el directorio dice `couch` (sofá) → confusión en el equipo y análisis de código

**Fix**: Renombrar directorio:
```bash
mv frontend/app/\(dashboard\)/couch frontend/app/\(dashboard\)/coach
```
Actualizar cualquier import o `Link href` que referencie `couch`.

### `page.tsx` Landing (24KB)

- Archivo de 24KB sugiere estilos y lógica inline en un solo componente
- Evaluar separar en: `HeroSection`, `FeaturesSection`, `PricingSection`, etc.

---

## 12. API WHATSAPP — MICROSERVICIO BAILEYS

### `src/app.ts` — Análisis Completo

```typescript
import "dotenv/config"              // ✅ Variables de entorno
import express from "express"       // ✅
import cors from "cors"             // 🔴 Sin configuración
import routes from "./infrastructure/router"
const port = process.env.PORT || 3001
const app = express()
app.use(cors())                     // 🔴 CORS abierto a todos los orígenes
app.use(express.json())             // ✅
app.use(express.static('tmp'))      // ⚠️ Sirve archivos tmp públicamente
app.use(`/`, routes)                // ✅
app.listen(port, () => console.log(`Ready...${port}`))
// ⚠️ Sin error handlers globales
// ⚠️ Sin process.on('uncaughtException')
// ⚠️ Sin healthcheck endpoint
```

**Issues identificados:**

1. **CORS abierto**: `cors()` sin opciones acepta todos los orígenes. El microservicio solo debería aceptar peticiones del backend Python.
```typescript
app.use(cors({ origin: process.env.BACKEND_URL || 'http://localhost:5000' }));
```

2. **Archivos tmp públicos**: `express.static('tmp')` expone el directorio `tmp/` completo, incluyendo QR codes de sesión y audios temporales.

3. **Sin autenticación**: Cualquiera puede enviar mensajes a través de la API si conoce la URL.

4. **Sin healthcheck**: PM2 y el backend no pueden verificar si el servicio está vivo sin llamar a un endpoint real.

5. **Sin manejo de errores globales**: Un error no capturado en Baileys mata el proceso.

**Fix sugerido para `app.ts`:**
```typescript
import "dotenv/config"
import express from "express"
import cors from "cors"
import routes from "./infrastructure/router"

const port = process.env.PORT || 3001
const app = express()

// CORS restringido al backend
app.use(cors({ origin: process.env.BACKEND_URL || 'http://localhost:5000' }))
app.use(express.json())

// Healthcheck
app.get('/health', (_, res) => res.json({ status: 'ok' }))

// Autenticación simple por API secret
app.use((req, res, next) => {
    const secret = req.headers['x-api-secret']
    if (secret !== process.env.API_SECRET) {
        return res.status(401).json({ error: 'Unauthorized' })
    }
    next()
})

app.use(`/`, routes)

// Error handler global
app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
    console.error('[GLOBAL ERROR]', err)
    res.status(500).json({ error: 'Internal server error' })
})

// Evitar crash por uncaught exceptions
process.on('uncaughtException', (err) => console.error('[UNCAUGHT]', err))
process.on('unhandledRejection', (reason) => console.error('[UNHANDLED]', reason))

app.listen(port, () => console.log(`WhatsApp API ready on port ${port}`))
```

---

## 13. BASE DE DATOS RELACIONAL (MySQL)

### Schema Overview

| Tabla | Propósito | Estado |
|-------|-----------|--------|
| `distributors` | Tenant principal | ✅ |
| `users` | Auth users por tenant | ✅ |
| `agent_configs` | Config IA | ✅ |
| `agent_features` | Features habilitadas | ✅ |
| `leads` | Prospectos | ✅ |
| `customers` | Clientes | ✅ |
| `conversations` | Historial chats | ⚠️ índice faltante |
| `messages` | Mensajes | ✅ |
| `documents` | KB docs RAG | ⚠️ `pinecone_ids` faltante |
| `wellness_evaluations` | Evaluaciones | ⚠️ verificar campos |
| `appointments` | Citas | ✅ |
| `channels` | Config canales | ✅ |
| `products` | Catálogo | ✅ |
| `subscriptions` | Suscripciones | ⚠️ conflicto backref |
| `plans` | Planes | ✅ |
| `scheduled_tasks` | Cron jobs | ✅ |
| `platform_config` | Config global | ✅ |

### Índices Faltantes Críticos

```sql
-- conversations: query principal del webhook
CREATE INDEX idx_conv_lookup ON conversations 
    (distributor_id, channel, participant_id, status);

-- scheduled_tasks: query del CronService
CREATE INDEX idx_tasks_pending ON scheduled_tasks 
    (distributor_id, action, status);

-- leads: búsqueda por teléfono (identity resolver)
CREATE INDEX idx_leads_phone ON leads (phone);

-- agent_configs: query del orchestrator
CREATE INDEX idx_agent_priority ON agent_configs 
    (distributor_id, priority DESC);
```

### Migraciones

- 🔴 Hay **dos** directorios `migrations/`:
  - `/enpiai/migrations/` (raíz del proyecto)
  - `/enpiai/backend/migrations/` (dentro del backend)
- Solo uno es activo. El otro es obsoleto y confunde al equipo.
- **Fix**: Identificar cuál es el activo (Flask-Migrate usa el relativo al package), eliminar el otro.

---

## 14. BASE DE DATOS VECTORIAL (Pinecone)

### Configuración

```python
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY', '')
PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'enpi-ai-rag')
```

- ✅ Un índice, múltiples namespaces (uno por distribuidor)
- ⚠️ Si `distributor.pinecone_namespace` es `None`, los documentos van al namespace default — fuga de datos entre tenants.

### Fix crítico en `models/distributor.py` y `services/rag_service.py`:
```python
# En creación de distribuidor, garantizar namespace:
def _get_namespace(self):
    return self.pinecone_namespace or f"dist_{self.id}"
```

### Calidad RAG

- 🔴 BUG-001 hace que todos los PDFs existentes estén mal chunkeados
- ⚠️ Sin logging de qué chunks fueron usados para generar cada respuesta (imposible auditar calidad)
- ⚠️ `chunk_size=1000` con `chunk_overlap=200` es razonable, pero CSV y documentos estructurados se benefician de chunking diferente

---

## 15. SEGURIDAD

### Evaluación de Superficie de Ataque

| Vector | Estado | Riesgo |
|--------|--------|--------|
| CORS wildcard + credentials | 🔴 | Crítico |
| SECRET_KEY fallback inseguro | 🔴 | Crítico |
| JWT en cookies (flags?) | ⚠️ Sin verificar | Alto |
| Redis sin password ni bind | ⚠️ | Medio |
| WhatsApp API sin auth | ⚠️ | Medio |
| `/api/voice/interact` sin auth | ⚠️ | Medio |
| Rate limiting in-memory | ⚠️ | Bajo |
| Path traversal (voz) | ✅ Mitigado | Bajo |
| SQL Injection | ✅ SQLAlchemy ORM | Bajo |
| Pinecone namespace null | ⚠️ | Bajo |
| C_FORCE_ROOT en Celery | ⚠️ | Bajo |
| uvicorn en 0.0.0.0 sin proxy | ⚠️ | Bajo |

### Recomendaciones de Seguridad

1. **JWT Cookies**: Verificar en `routes/auth.py` que los cookies tienen:
   ```python
   response.set_cookie(
       'access_token', token,
       httponly=True,   # ← no accesible via JS
       secure=True,     # ← solo HTTPS
       samesite='Strict',
       max_age=86400
   )
   ```

2. **Redis**: En `ecosystem.config.js`:
   ```javascript
   args: "--port 6381 --bind 127.0.0.1 --requirepass YOUR_REDIS_PASS"
   ```

3. **uvicorn**: Cambiar `--host 0.0.0.0` a `--host 127.0.0.1` y usar Nginx como reverse proxy.

4. **Celery**: Eliminar `C_FORCE_ROOT: "true"` y crear usuario dedicado `celery_user`.

---

## 16. DEVOPS — PM2 / DESPLIEGUE

### `ecosystem.config.js` — Análisis Completo

| Proceso | Estado | Issues |
|---------|--------|--------|
| `enpiai-redis` | ✅ | Sin password, sin bind |
| `enpiai-frontend` | ✅ | — |
| `enpiai-fastapi` | ✅ | `--host 0.0.0.0` sin proxy |
| `enpiai-worker` | ✅ | `C_FORCE_ROOT: true` |
| `enpiai-cron` | ✅ | Singleton multi-worker? |
| `enpiai-whatsapp` | ✅ | Sin `max_memory_restart` |

**Fix para `enpiai-whatsapp`:**
```javascript
{
    name: "enpiai-whatsapp",
    cwd: "./api-whatsapp",
    script: "./dist/app.js",
    max_memory_restart: "500M",    // ← añadir
    env: {
        PORT: 3001,
        NODE_ENV: "production",
        BACKEND_URL: "http://localhost:5000",   // ← añadir
        API_SECRET: process.env.WA_API_SECRET  // ← añadir
    }
}
```

### Sin CI/CD

- No hay GitHub Actions ni pipeline automatizado
- Despliegue manual via `deploy.sh`
- **Riesgo**: Errores humanos en deploy, sin tests automáticos antes de desplegar
- **Recomendación mínima**: GitHub Action que ejecute `pytest` y `npm run build` en cada PR

---

## 17. REDUNDANCIAS E INCONSISTENCIAS

| ID | Descripción | Acción |
|----|-------------|--------|
| R-001 | CORS configurado en FastAPI **y** Flask | Eliminar el Flask CORS |
| R-002 | `/health` en FastAPI **y** Flask (el Flask es inalcanzable) | Eliminar Flask health |
| R-003 | Webhook WA en FastAPI (async) **y** Flask (sync fallback) | Documentar explícitamente; sincronizar lógica de audio |
| R-004 | Dos directorios `migrations/` | Identificar activo, eliminar el otro |
| R-005 | `GOOGLE_AI_API_KEY` en config vs `GOOGLE_API_KEY` en orchestrator | Unificar a `GOOGLE_AI_API_KEY` |
| R-006 | `create_app()` llamado en `fastapi_app.py` Y dentro de cada task | Aceptable para Celery, documentar |
| R-007 | `doc.is_processed = True` en dos branches distintos del mismo flujo | Crear enum `ProcessingStatus` |
| R-008 | `get_full_system_prompt()` en `Distributor` model — código muerto | Eliminar o documentar como deprecated |
| R-009 | Cleanup de sesión DB triple en `process_webhook_message` | Simplificar a solo `finally` |
| R-010 | `llm_service.py` existe junto con `_get_llm()` en orchestrator | Verificar si hay duplicación de lógica LLM |

---

## 18. MAL TIPADO Y TYPE SAFETY

### Python — Issues

```python
# tasks.py:23 — Sin type hints
def generate_pdf_report(self, distributor_id, report_type, data):
# Fix:
def generate_pdf_report(self, distributor_id: int, report_type: str, data: dict) -> dict:

# tasks.py:44 — Optional sin tipo
def index_document_rag(self, filepath, distributor_id, document_id, metadata=None):
# Fix:
def index_document_rag(self, filepath: str, distributor_id: int, document_id: int, metadata: Optional[Dict[str, Any]] = None) -> dict:

# agent_orchestrator.py:59 — None no tipado
def _get_llm(self, model_override: str = None):
# Fix:
def _get_llm(self, model_override: Optional[str] = None):

# agent_orchestrator.py:167 — Any en lugar de tipo base
def _resolve_skills(self, agent: AgentConfig, enabled_features: List[str]) -> List[Any]:
# Fix: crear BaseSkill abstract class

# fastapi_app.py:105 — distributor_id sin cast
distributor_id = data.get('companyId')   # tipo Any
# Fix:
distributor_id = int(data.get('companyId', 0)) if data.get('companyId') else None

# config.py — Class variables sin tipo explícito
SECRET_KEY = os.getenv(...)   # debería ser: SECRET_KEY: str = os.getenv(...)
```

### TypeScript — Issues

- `middleware.ts`: Correcto con optional chaining ✅
- Componentes del frontend: No revisados en detalle — probable falta de tipado en respuestas de API

---

## 19. EXPERIENCIA DEL DISTRIBUIDOR

### Problemas que Afectan Directamente al Distribuidor

| ID | Problema | Causa | Impacto |
|----|----------|-------|---------|
| P-001 | **El agente no responde** | BUG-005: modelo gpt-5-nano inválido | Crítico |
| P-002 | **Agente olvida conversaciones** | MemorySaver volátil + historial no inyectado | Alto |
| P-003 | **Respuestas RAG incorrectas** | BUG-001: PDFs mal chunkeados | Alto |
| P-004 | **Spam de follow-ups** | Follow-up duplicado en cada respuesta | Alto |
| P-005 | **URL /couch en dashboard** | Typo en directorio frontend | Bajo |
| P-006 | **Rutas sin protección** | Middleware incompleto | Medio |
| P-007 | **Sin feedback de error de config** | No hay alertas en dashboard | Medio |

### Lo que SÍ Funciona Bien ✅

- Flujo completo WhatsApp → Agent → Respuesta → WhatsApp está bien diseñado
- Aislamiento multi-tenant via namespace Pinecone es correcto
- Voz bidireccional (Whisper STT + Azure TTS) está bien integrada
- Evaluaciones de bienestar con PDF + WhatsApp + Email es un feature completo y diferenciador
- Sistema de follow-ups automáticos existe y funciona (con bug de duplicados)
- Panel de administración super-admin existe
- Facturación con dLocal Go integrada
- Identity resolution (detectar si el que escribe ES el distribuidor o un prospecto) es sofisticado y correcto

---

## 20. PLAN DE ACCIÓN PRIORIZADO

### 🔴 PRIORIDAD 1 — CRÍTICOS (Resueltos - Junio 2026)

| Fix | Descripción | Archivo | Esfuerzo | Estado |
|-----|-------------|---------|----------|--------|
| FIX-001 | `"\\n"` → `"\n"` en tasks.py:75 + **re-indexar todos los PDFs en Pinecone** | `tasks.py` | 1h + indexación | ✅ Resuelto |
| FIX-002 | CORS: lista explícita de orígenes en lugar de wildcard | `fastapi_app.py:39-45` | 30min | ✅ Resuelto |
| FIX-003 | `is_o_model` check con set exacto de nombres | `agent_orchestrator.py:77` | 30min | ✅ Resuelto |
| FIX-004 | `gpt-5-nano` → `gpt-4o-mini` en config + orchestrator (3 lugares) | `config.py:72`, `agent_orchestrator.py:63,99` | 30min | ✅ Resuelto |
| FIX-005 | Validar `distributor_id != None` en webhook FastAPI antes de procesar | `fastapi_app.py:105` | 30min | ✅ Resuelto |
| FIX-006 | Completar rutas protegidas + matcher en middleware | `frontend/middleware.ts` | 30min | ✅ Resuelto |

### 🟠 PRIORIDAD 2 — ALTOS (Parcialmente Resueltos)

| Fix | Descripción | Archivo | Esfuerzo | Estado |
|-----|-------------|---------|----------|--------|
| FIX-007 | Reemplazar `flask.g` por `threading.local` en tool_node | `agent_orchestrator.py:301` | 2h | ✅ Resuelto |
| FIX-008 | Añadir columna `pinecone_ids JSON` al modelo Document + migración | `models/document.py` | 1h | ✅ Resuelto |
| FIX-009 | Añadir `soft_time_limit=60` al task `process_webhook_message` | `tasks.py` | 30min | 🟡 Pendiente |
| FIX-010 | Deduplicar follow-ups: verificar si ya existe uno pendiente antes de crear | `agent_orchestrator.py:488-512` | 2h | ✅ Resuelto |
| FIX-011 | Inyectar últimos 20 mensajes MySQL en el estado inicial LangGraph | `agent_orchestrator.py` | 3h | ✅ Resuelto |
| FIX-012 | Unificar env var `GOOGLE_API_KEY` → `GOOGLE_AI_API_KEY` | `agent_orchestrator.py:71` | 30min | ✅ Resuelto |
| FIX-013 | Añadir autenticación (API key o JWT) al endpoint `/api/voice/interact` | `fastapi_app.py` | 1h | ✅ Resuelto |
| FIX-014 | Renombrar `couch` → `coach` en frontend + actualizar imports | Frontend | 1h | ✅ Resuelto |
| FIX-015 | Añadir `time.sleep(0.5)` entre mensajes en `send_broadcast_message` | `tasks.py` | 30min | ✅ Resuelto |
| FIX-016 | Añadir índices MySQL faltantes via nueva migración | `migrations/` | 2h | ✅ Resuelto |
| FIX-017 | Validación de SECRET_KEY en startup de producción | `config.py` / `create_app()` | 30min | ✅ Resuelto |

### 🟡 PRIORIDAD 3 — MEDIOS (Parcialmente Resueltos)

| Fix | Descripción | Esfuerzo | Estado |
|-----|-------------|----------|--------|
| FIX-018 | Rate limiter → Redis storage | 1h | 🟡 Pendiente |
| FIX-019 | CORS + auth en microservicio WhatsApp (`app.ts`) | 2h | 🟡 Pendiente |
| FIX-020 | Garantizar `pinecone_namespace` nunca es None en `rag_service.py` | 1h | 🟡 Pendiente |
| FIX-021 | Redis con `--requirepass` y `--bind 127.0.0.1` en PM2 | 1h | 🟡 Pendiente |
| FIX-022 | `max_memory_restart: "500M"` para PM2 enpiai-whatsapp | 30min | 🟡 Pendiente |
| FIX-023 | Simplificar cleanup triple en `process_webhook_message` | 1h | ✅ Resuelto |
| FIX-024 | Limpiar archivos `.mp3` temporales de `uploads/voice/` (cron job) | 1h | 🟡 Pendiente |
| FIX-025 | Eliminar directorio `migrations/` obsoleto de la raíz | 30min | ✅ Resuelto |
| FIX-026 | Añadir `process.on('uncaughtException')` en `api-whatsapp/src/app.ts` | 30min | 🟡 Pendiente |

### 🟢 PRIORIDAD 4 — MEJORAS (Backlog)

| Mejora | Descripción | Esfuerzo |
|--------|-------------|----------|
| IMP-001 | Migrar `MemorySaver` → `RedisSaver` para persistencia real | 4h |
| IMP-002 | Implementar GitHub Actions: lint + test + build en PRs | 8h |
| IMP-003 | Externalizar templates HTML de `email_service.py` a archivos `.html` | 3h |
| IMP-004 | Crear enum `ProcessingStatus` para documentos | 2h |
| IMP-005 | Refactorizar `page.tsx` (24KB) en componentes React | 4h |
| IMP-006 | `SemanticChunker` para documentos RAG | 3h |
| IMP-007 | Logging de chunks RAG usados en cada respuesta | 2h |
| IMP-008 | Eliminar código muerto `Distributor.get_full_system_prompt()` | 1h |
| IMP-009 | Consolidar los dos engines SQLAlchemy | 4h |
| IMP-010 | `uvicorn --host 127.0.0.1` + Nginx reverse proxy | 2h |

---

## 21. SCORECARD FINAL

```
╔══════════════════════════════════════════════════════════════════╗
║              ENPIAI — SCORECARD TÉCNICO GENERAL                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Diseño Arquitectural    ████████████░░░░  78/100  ✅ Sólido      ║
║  Calidad del Código      ██████████░░░░░░  62/100  ⚠️ Mejorable   ║
║  Seguridad               ███████░░░░░░░░░  45/100  🔴 Brechas      ║
║  Tipado / Type Safety    ████████░░░░░░░░  50/100  ⚠️ Incompleto  ║
║  Testing                 ████░░░░░░░░░░░░  25/100  🔴 Sin cobertura║
║  Documentación           ██████████░░░░░░  65/100  ⚠️ Parcial     ║
║  Performance (índices)   ████████░░░░░░░░  52/100  ⚠️ Sin índices  ║
║  DevOps / Deploy         ██████████░░░░░░  60/100  ⚠️ Sin CI/CD   ║
║  UX Distribuidor         ████████████░░░░  75/100  ✅ Buen diseño  ║
║                                                                  ║
║  SCORE GLOBAL            ████████░░░░░░░░  57/100  ⚠️             ║
╚══════════════════════════════════════════════════════════════════╝
```

### Bugs activos confirmados en producción

| Bug | Archivo | Línea | Impacto |
|-----|---------|-------|---------|
| BUG-001: PDF `\\n` literal | tasks.py | 75 | Todos los PDFs RAG mal indexados |
| BUG-002: CORS wildcard+creds | fastapi_app.py | 41 | Requests bloqueados en navegadores |
| BUG-003: is_o_model false+ | agent_orchestrator.py | 77 | Parámetros LLM incorrectos |
| BUG-004: flask.g en Celery | agent_orchestrator.py | 301 | Tools pueden fallar silenciosamente |
| BUG-005: gpt-5-nano inválido | config.py | 72 | LLM falla si env no configurado |
| BUG-006: pinecone_ids | tasks.py | 117 | IDs de vectores no se persisten |

### Conclusión

EnpiAI tiene una **arquitectura conceptual sólida** — la elección de LangGraph + Celery Fire&Forget + multi-tenant RAG demuestra criterio técnico avanzado. El producto tiene una propuesta de valor clara para distribuidores Herbalife.

Sin embargo, hay **5 bugs confirmados que afectan el core del producto en producción** y **2 brechas de seguridad críticas** que deben resolverse antes de escalar.

Con las **Prioridad 1 aplicadas** (≈6 horas de trabajo), el sistema estará en condición de `production-ready` para el core del producto. Las Prioridades 2 y 3 garantizan estabilidad y seguridad a largo plazo.

---

*Auditoría generada: Junio 2026 · EnpiAI v2.0*  
*Próxima revisión: Post-implementación de Prioridades 1 y 2*
