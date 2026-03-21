# Project Analysis Summary: EnpiAI

**Project Name**: Herbalife Distributor SaaS Platform
**Current State**: Advanced Development Phase / Scaffolding & Core Logic Implemented.

## 1. Documentation Overview
The project has excellent documentation that serves as the "Source of Truth":
- **`GEMINI.md`**: Core AI development guidelines and project vision.
- **`README.md`**: General overview and setup instructions.
- **`AGENTS.md`**: Detailed multi-agent architecture (Orchestrator, SkillAdapter).
- **`DEVELOPMENT_GUIDE.md`**: Technical manual for developers.
- **`SKILL_Agentic-Engineering-Protocol_IAGS.md`**: Theoretical framework for agentic engineering and data sovereignty.
- **`backend/ANALYSIS_BACKEND.md`**: Ultra-detailed technical analysis of the backend.
- **`frontend/FRONTEND_GUIDE.md`**: Comprehensive guide for the Next.js frontend.

## 2. Backend Analysis (Python/Flask)
The backend is a robust modular application using **Flask 3.0**.
- **Orchestration**: Uses **LangGraph** for sophisticated agent workflows with state management and memory checkpointing (Redis/Memory).
- **LLM Service**: Implements a `SkillAdapter` with **failover cascade** (OpenAI -> Anthropic -> Google Gemini).
- **Data Layer**: **MySQL** (via SQLAlchemy) for relational data and **Pinecone** for vector memory (RAG).
- **Asynchronous Processing**: **Celery** with Redis is used for long-running tasks like PDF generation (ReportLab) and RAG indexing.
- **Security**: JWT-based authentication, Google OAuth integration, and application-level encryption for sensitive data.

## 3. Frontend Analysis (Next.js 14+)
The frontend uses the modern **App Router** architecture.
- **Stack**: Next.js, TypeScript, Tailwind CSS, Shadcn UI, Radix UI, TanStack Query (React Query), and Zustand.
- **Key Modules**:
    - **Auth**: Login and registration flows implemented.
    - **Dashboard**: Operational metrics and CRM views (Leads, Customers).
    - **CRM**: Unified contact view with a 360° timeline.
    - **Agent Config**: Dynamic configuration of personas and features.
    - **Public Evaluation**: Landing pages for wellness evaluations.
- **UX**: Focuses on "Zero Friction" with skeletons, dark mode support, and mobile-first design.

## 4. External Services
- **`api-whatsapp`**: A dedicated Node.js service for WhatsApp multi-tenant connectivity. It uses various engines (`baileys`, `whatsapp-web.js`, `venom-bot`) and integrates directly with MySQL.
- **Telegram Integration**: Planned/Implemented via `python-telegram-bot`.
- **Google Integration**: Calendar and Gmail APIs for scheduling and automated follow-ups.

## 5. Current Progress vs. Goals
- ✅ Project Scaffolding & Core Architecture Logic.
- ✅ Multi-Agent Orchestration (LangGraph, Failover strategy).
- ✅ Hybrid Architecture (SQL + Vector Pinecone).
- ✅ Integración Multi-Tenancy WhatsApp (QR Flow asíncrono, persistencia de conexión por distribuidor).
- ✅ Backend I18n (EN/ES/FR/PT).
- ✅ Universal RAG Management (Documentos globales para el Super Administrador y búsqueda concurrente con namespace local).
- ✅ Agent-Driven Lead Capture (El agente prioriza conseguir nombre y teléfono antes de usar herramientas para registrar el contacto).
- ✅ Personalized Wellness Evaluation Links (URL pública con ID oficial de Herbalife `herbalife_id` para captura de plomos atribuidos correctamente).
- ✅ Deployment Scripts: Scripts locales (`start-local.sh`, PM2 ecosystem) listos.
- 🚧 UI/UX Dashboard Frontend (Tablas de contactos, reportes de evaluación en progreso).
- 🚧 Generación de PDFs y flujos asíncronos en Celery (Operativos pero puliéndose).

**Verdict**: The project is in an **Advanced / Pre-Production State**. The core "Agentic Infrastructure" (IAGS protocol) is fully functional: the multi-agent orchestrator understands anonymous users, dynamically fetches context from vector DBs, delegates tasks to tools (like `CaptureContact`), and flawlessly receives messages from the custom WhatsApp Gateway (`api-whatsapp/`). The crucial milestone of isolating logic per `distributor_id` (and `herbalife_id` routing) is structurally sound across Next.js, Flask, and Node.js. The next immediate focus should be finalizing frontend UI panels for CRMs and ensuring the Celery infrastructure is rock solid for production.
