
# GEMINI.md - AI Development Context & Guidelines

**Copyright © 2026 WEBLIFETECH (Jonnathan Peña). All Rights Reserved.**

This document provides the **SINGLE SOURCE OF TRUTH** for the Herbalife Distributor SaaS Platform, combining high-level vision with strict technical constraints. **ALL AI AGENTS MUST ADHERE TO THIS DOCUMENT.**

---

## 🧠 AI Agent Coding Protocol (Mandatory)

> [!IMPORTANT]
> **ALL AI AGENTS MUST FOLLOW THESE RULES TO MAINTAIN SYSTEM INTEGRITY.**

### 1. Database Stability & Resiliency
To prevent "MySQL has gone away" errors and stale transactions:
- **Rule**: Execute `db.session.rollback()` at the absolute start of every tool function, webhook, or service entry point.
- **Pattern**:
    ```python
    def my_service_function():
        from extensions import db
        db.session.rollback()  # Mandatory first line
        # ... logic
    ```

### 2. Multi-Tenancy (Tenant Isolation)
- **Rule**: Every query involving distributor-owned data **MUST** filter by `distributor_id`.
- **Constraint**: Never assume the distributor context; always retrieve from `g.current_company` or explicit parameters.

### 3. Data Sovereignty & PII Protection
- **Rule**: All Personally Identifiable Information (PII) must be encrypted at the application level.
- **Pattern**:
    ```python
    from services.encryption_service import EncryptedString, EncryptedJSON
    
    class MyModel(db.Model):
        phone = db.Column(EncryptedString(500))  # Mandatory for PII
        config = db.Column(EncryptedJSON)        # Mandatory for secrets
    ```

---

## 🛠 Technical Architecture (The "Stack")

### 1. Core Services (HTA Architecture)
- **Agent Orchestrator**: LangGraph-based state machine with `MemorySaver` / `RedisSaver`.
- **LLM Adapter**: Unified gate using `langchain_openai`, `langchain_anthropic`, and `langchain_google_genai` with a failover cascade.
- **RAG Memory**: Pinecone serverless with namespace-isolated indexes (`namespace=dist_ID`).

### 2. Frontend (Next.js 14+ App Router)
- **State Management**: `TanStack Query` (Server State) + `Zustand` (Client State).
- **UI Components**: `Shadcn UI` + `Tailwind CSS` + `Lucide React`.
- **Internationalization**: `react-i18next` synchronized with backend `I18nService`.

---

## 🔒 Critical Rules & Constraints (Zero Tolerance)

1.  **Consensual Scheduling**: Agents **CANNOT** book a calendar slot without explicit confirmation from the user.
2.  **Sovereign Data**: Sensitivity to PII is absolute. Never log raw phone numbers or emails.
3.  **Migration Path**: Every new module MUST include a comment: `"Migration Path: How this SQL/Logic moves to a decentralized P2P state."`
4.  **No Lazy Loading**: Avoid accessing related DB objects in loops. Prefer joined loads or separate queries into primitives.

---

## ✅ Integration Status

| Component | Status | Details |
| :--- | :--- | :--- |
| **Auth** | 🟢 Ready | JWT + Google OAuth + Refresh Tokens |
| **Database** | 🟢 Ready | Remote MySQL + Pinecone (Namespaced) |
| **Orchestration** | 🟢 Ready | LangGraph + Redis Persistence |
| **RAG** | 🟢 Ready | PDF/Docx uploads + Semantic Search |
| **Scheduling** | 🟢 Ready | Google Calendar (Consensual) |
| **Payments** | 🟡 Testing | dLocal integration for subscriptions |
| **CRM** | 🟢 Ready | Unified 360° Contact Profile + Timeline |
| **WhatsApp** | 🟢 Ready | `api-whatsapp` local microservice (Multi-tenant) |
| **Telegram** | 🟢 Ready | `python-telegram-bot` integrated |
| **Email** | 🟢 Ready | SMTP + SendGrid support |

---

## 📂 Project Structure Map

### 1. Backend Blueprints (`backend/routes/`)
*   **auth.py**: Authentication, registration, and Google OAuth.
*   **contacts.py**: Unified contact persistence and timeline aggregation.
*   **agents.py**: LangGraph orchestrator and tool definitions.
*   **wellness.py**: Evaluation logic and PDF report generation (Celery).
*   **rag.py**: Vector memory and multi-tenant document management.
*   **openai_compat.py**: OpenAI-standard API bridge for external tools.

### 2. Frontend (Next.js 14+ App Router)
*   **/(dashboard)/contacts**: Multi-tenant CRM view with 360° timeline.
*   **/(dashboard)/agents**: Dynamic configuration of AI personas and features.
*   **/(dashboard)/documents**: Knowledge base management with RAG status.
*   **/wellness/[dist_id]**: Public health assessment forms with attribution.
*   **/locales**: EN, ES, PT translation files.
