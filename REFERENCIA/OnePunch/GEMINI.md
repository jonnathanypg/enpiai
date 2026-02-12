# GEMINI.md - AI Development Context & Guidelines

**Copyright © 2026 WEBLIFETECH (Jonnathan Peña). All Rights Reserved.**

This document provides the **SINGLE SOURCE OF TRUTH** for the OnePunch architecture, combining high-level vision with strict technical constraints. **ALL AI AGENTS MUST ADHERE TO THIS DOCUMENT.**

---

## 🧠 Core Vision

**OnePunch** is a customizable, multi-agent SaaS ecosystem designed to function as a complete 360° virtual workforce. It orchestrates specialized agents ("Chefs") to handle complex business flows via a unified interface.

*   **Orchestration**: **LangGraph** (Stateful, Persistent, Cyclical graphs).
*   **Intelligence**: Hybrid Approach (RAG + Multi-LLM + Sentiment Analysis).
*   **Goal**: Full automation of Scheduling, Sales, Support, and Payments.

---

## 🛠 Technical Architecture (The "Stack")

### 1. Data Layer
*   **Relational DB**: **Remote MySQL** (Primary).
    *   *Constraint*: Critical strictness on `db.session.rollback()` usage.
*   **Vector DB**: **Pinecone** v5.0+ (`text-embedding-3-small`, 1536 dims).
*   **ORM**: SQLAlchemy 2.0+ with `pool_pre_ping=True` and `pool_recycle=10` (Self-Healing).

### 2. Core Services (`/services`)
*   **`langgraph_agent.py`**: The BRAIN. Orchestrates state using `langgraph>=1.0.0`.
*   **`langgraph_tools.py`**: The HANDS. Wraps integrations (Google, PayPal, etc.).
*   **`rag_service.py`**: Handles Vector I/O. Uses **ThreadPoolExecutor** for non-blocking document uploads.
*   **`llm_service.py`**: Unified gateway for OpenAI, Anthropic, and **Google Gemini** (`google-generativeai`).
*   **`sentiment_service.py`**: Analyzes interactions using NLTK/TextBlob.
*   **`pdf_service.py`**: Generates invoices/receipts using `reportlab`.

### 3. Integrations (`/integrations`)
*   **Google**: Calendar & Sheets via `google-api-python-client`.
*   **PayPal**: `paypal-agent-toolkit` & `paypalrestsdk` for checkout flows.
*   **HubSpot**: `hubspot-api-client` v8+ for CRM sync.
*   **LiveKit**: `livekit-agents` for Realtime Voice (WebRTC).

---

## 🔒 Critical Rules & Constraints (Zero Tolerance)

### A. Database Stability (The "Gone Away" Fix)
1.  **Preventive Rollbacks**: You **MUST** execute `db.session.rollback()` at the absolute start of any Tool function or Service entry point.
2.  **No Lazy Loading in Loops**: Never access `agent.features` or `company.settings` inside long-running processes.
    *   *Correct Pattern*: Load config into Python primitives (lists/dicts) **BEFORE** starting the workflow.

### B. Environment & Security
*   **No Hardcoding**: All secrets must be in `.env`.
*   **Critical Env Vars**: `OPENAI_API_KEY`, `PINECONE_API_KEY`, `DATABASE_URL`, `PAYPAL_CLIENT_ID`, `GOOGLE_CLIENT_ID`.
*   **Google Auth**: `GOOGLE_CREDENTIALS_JSON` (Base64) or `client_secret.json` path.

### B. Business Logic Enforcements
1.  **Consensual Scheduling**:
    *   The Agent **CANNOT** book a slot without explicit user confirmation ("Yes, book 3 PM").
    *   If `check_availability` fails, present options and **WAIT**.
2.  **Payment Flows**:
    *   **Identity First**: `lookup_customer` is mandatory before showing price.
    *   **Email Sync**: If user requests a receipt/summary, `send_email` IS MANDATORY. You cannot "simulate" it in chat.
3.  **Flow Isolation**:
    *   Payment Context (Money, Invoices) != Agenda Context (Dates, Times).
    *   The prompt uses a **Flow Context System** to prevent hallucinations between these modes.

---

## 📋 Development Workflow

**Branching Strategy**:
1.  `main`: **PRODUCTION**. Read-only for AI.
2.  `dev`: **STAGING**. The target for all merges.
3.  `feature/[name]`: **WORKING**. Create this for every task.

**Commit Protocol**:
1.  **Create Artifact**: `task.md` (Checklist).
2.  **Code**: Implement changes.
3.  **Verify**: Run the code.
4.  **Log**: Update `docs/development_log.md` (Required).
5.  **Merge**: `feature` -> `dev`.

---

## ✅ Integration Status (Jan 2026)

| Component | Status | Details |
| :--- | :--- | :--- |
| **Auth** | 🟢 Ready | JWT + Google OAuth |
| **Database** | 🟢 Stable | Remote MySQL + Pinecone |
| **Orchestration** | 🟢 Ready | LangGraph (Stateful) |
| **RAG** | 🟢 Ready | Uploads (PDF/Docx) + Querying |
| **Scheduling** | 🟢 Ready | Google Calendar (Timezone Aware) |
| **Payments** | 🟢 Ready | PayPal (Sandbox/Live) + Receipts |
| **CRM** | 🟢 Ready | HubSpot + Custom Customer Model |
| **Sentiment** | 🟢 Ready | Automatic Analysis + Escalation |
| **Voice** | 🟡 Alpha | LiveKit Integration present |
| **Email** | 🟢 Ready | SendGrid Transactional |

---

## 📂 Project Structure Map

### 1. Backend Blueprints (`routes/`)
*   **Auth**: `auth.py`, `google_auth.py`, `hubspot_auth.py` (OAuth flows).
*   **Core**: `companies.py` (Settings), `employees.py` (Team), `agents.py` (Config), `channels.py` (Integrations).
*   **Features**: `rag.py` (Docs), `chat.py` (Admin Chat), `analytics.py` (Dashboard Stats).
*   **External**: `webhooks.py` (Twilio/Messaging), `payments.py` (PayPal/Stripe), `voice_agent_api.py` (LiveKit).

### 2. Frontend Templates (`templates/`)
*   **Base**: `base.html` (Master Layout + Sidebar).
*   **Auth**: `auth/login.html`, `auth/register.html`.
*   **Dashboard**: `dashboard/index.html` (Stats), `dashboard/chat.html` (AI Interface).
*   **Config**: `config/agents.html`, `config/channels.html`, `config/settings.html`.
*   **Public**: `payment/success.html`, `payment/cancel.html`.

### 3. Data Models (`models/`)
*   **Tenancy**: `Company` (Root), `User` (Admin).
*   **Actors**: `Agent` (AI Config), `Employee` (Humans).
*   **Business**: `Customer` (Leads), `Appointment` (Calendar), `Transaction` (Money).
*   **System**: `Document` (RAG), `Conversation`/`Message` (Logs), `Channel` (Integrations).