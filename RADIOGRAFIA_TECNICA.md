# 🩻 EnpiAI - Technical X-Ray (Project Status Report)
**Date:** May 16, 2026
**Version:** 1.0.0 (Post-WhatsApp Intelligence Upgrade)
**Ownership:** WEBLIFETECH (Jonnathan Peña)

This document provides a comprehensive, hyper-detailed technical overview of the EnpiAI Herbalife Distributor SaaS Platform. It is designed to be the definitive guide for AI agents and senior developers to understand the architecture, flows, and current state of the codebase.

---

## 🏗️ 1. System Architecture Overview

The system follows a **Modular Micro-Monolith** approach with specialized service layers and a dedicated WhatsApp microservice.

- **Primary Backend:** Flask (Python 3.10+) - Handles API, Orchestration, and Business Logic.
- **Secondary Backend:** FastAPI (Python) - Used for high-performance specialized tasks.
- **WhatsApp Gateway:** Node.js/TypeScript (Baileys) - Multi-tenant WhatsApp session management.
- **Frontend:** Next.js 14+ (App Router) - Modern React interface with TanStack Query and Zustand.
- **Async Processing:** Celery + Redis - Handles heavy lifting (PDFs, AI Diagnosis, RAG indexing).
- **Database:** 
    - **Relational:** MySQL - Primary storage for tenants, leads, and conversations.
    - **Vector:** Pinecone - RAG memory for distributor knowledge bases.
    - **Cache/Queue:** Redis - Broker for Celery and potentially for state persistence.

---

## 🐍 2. Backend Deep Dive (Python/Flask)

### 📂 Directory Structure (`/backend`)
- `/routes`: API blueprints grouped by domain (auth, leads, wellness, webhooks, etc.).
- `/models`: SQLAlchemy models defining the relational schema.
- `/services`: Core business logic (Orchestrator, RAG, Messaging, Cron).
- `/skills`: Modular LangGraph tools (CRM, Wellness, Scheduler, Knowledge Base).
- `/venv`: Python virtual environment.
- `app.py`: Application factory and blueprint registration.
- `tasks.py`: Celery background task definitions.

### 🧠 Agent Orchestration (LangGraph)
- **File:** `backend/services/agent_orchestrator.py`
- **Engine:** `StateGraph` with `MemorySaver`.
- **Flow:** `agent_node` (Reasoning) -> `should_continue` (Routing) -> `tool_node` (Execution).
- **Intelligence:**
    - **Multi-Tenant Prompting:** `SystemPromptBuilder` constructs unique prompts per distributor.
    - **Modular Skills:** Tools are injected dynamically based on `AgentConfig` features.
    - **Identity Resolution:** Detects if the sender is the Distributor (Master Mode) or a Lead.
    - **Sentiment Analysis:** Keyword-based fast analysis to detect escalation risks.

### 📜 Database Models (`/backend/models`)
- `User`: Authentication (Email/Password + Google OAuth).
- `Distributor`: Root tenant. Stores `herbalife_id`, business settings, and AI persona.
- `Lead`: Potential customers. Includes PII (Encrypted phone/email).
- `Conversation`: Tracks chat history across WhatsApp/Telegram/Webchat.
- `WellnessEvaluation`: Stores health data, AI diagnosis, and PDF paths.
- `ScheduledTask`: Persists background jobs for `CronService`.

---

## 🟢 3. WhatsApp Gateway (Node.js/TypeScript)

### 📂 Directory Structure (`/api-whatsapp`)
- `src/infrastructure/repositories/baileys.repository.ts`: Core WhatsApp logic.
- `src/infrastructure/ioc.ts`: Event listeners and backend forwarding.
- `src/application/lead.create.ts`: Message sending logic.

### ⚙️ Key Technical Features
- **Multi-Tenancy:** One `WASocket` session per `companyId`.
- **Authentication:** Sessions stored in MySQL (`bailey_sessions` table) using a custom Auth State.
- **Events Forwarded to Backend:**
    - `message`: Incoming text/media messages.
    - `call`: Audio/Video call attempts (Forwarded as system messages).
- **Media Handling:** Automatically downloads documents/images to `tmp/uploads` and notifies Python.

---

## 🎨 4. Frontend Deep Dive (Next.js)

### 📂 Structure (`/frontend`)
- `app/`: Next.js 14 App Router.
    - `(auth)`: Login/Register flows.
    - `(dashboard)`: Main CRM and configuration interface.
    - `(public)`: Public forms (Wellness Evaluation).
- `services/`: API client wrappers (Axios).
- `store/`: Zustand stores for client state.

### 🛠️ Tech Stack
- **Styling:** Tailwind CSS + Shadcn UI.
- **State:** TanStack Query (Server State) + Zustand (UI State).
- **Forms:** React Hook Form + Zod validation.
- **Auth:** JWT stored in cookies.

---

## ⚡ 5. Critical Workflows

### 📩 Message Flow (WhatsApp -> AI -> WhatsApp)
1. **Baileys** receives message -> `ioc.ts` catches it.
2. `ioc.ts` POSTs to `backend/webhooks/whatsapp`.
3. Flask saves message to `db` and dispatches `process_webhook_message` to **Celery**.
4. **Celery Worker** runs `AgentOrchestrator`:
    - Generates system prompt via `SystemPromptBuilder`.
    - Invokes LangGraph with thread persistence.
    - Agent uses `skills` (CRM, RAG, etc.) if needed.
5. `MessagingService` splits long responses and sends them back to Node.js.
6. Node.js sends messages to the physical device.

### 🏥 Wellness Evaluation Flow
1. Lead fills form at `enpi.ai/wellness/[herbalife_id]`.
2. Flask POST `/api/wellness/evaluate/[ref]` creates `Lead` and `WellnessEvaluation`.
3. Dispatches `process_wellness_evaluation` to **Celery**.
4. **Celery Worker**:
    - Calls AI for Diagnosis/Recommendations.
    - Generates PDF using `pdf_service` (ReportLab).
    - Sends PDF via WhatsApp and Email.
    - Notifies Distributor via WhatsApp.

### ⏰ Follow-up Logic (Cron)
- `CronService` runs a background thread + PM2 process.
- **24h Rule:** Schedules Step 1 (Subtle check-in).
- **48h Rule:** Schedules Step 2 (Value-added tip) if Step 1 wasn't answered.
- **Automatic Cancellation:** Any user message cancels pending `auto_followup` tasks.

---

## 🔒 6. Security & Protocols (GEMINI.md Mandates)
- **DB Rollback:** Every service entry point MUST call `db.session.rollback()` first.
- **PII Encryption:** Phone numbers and emails MUST use `EncryptedString`.
- **Tenant Isolation:** All queries MUST filter by `distributor_id`.
- **O-Model Handling:** GPT-5/o1 models use `max_completion_tokens` and temperature 1.0.

---

## 🚀 7. Infrastructure (PM2 / Deployment)
Managed by `ecosystem.config.js`:
- `enpiai-redis`: Port 6381.
- `enpiai-backend`: Gunicorn (Flask).
- `enpiai-worker`: Celery Worker.
- `enpiai-whatsapp`: Node.js process.
- `enpiai-cron`: Python process for scheduled tasks.

---
*Fin del reporte técnico.*
