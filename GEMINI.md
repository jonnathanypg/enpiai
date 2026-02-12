
# GEMINI.md - AI Development Context & Guidelines

**Copyright © 2026 WEBLIFETECH (Jonnathan Peña). All Rights Reserved.**

This document provides the **SINGLE SOURCE OF TRUTH** for the Herbalife Distributor SaaS Platform, combining high-level vision with strict technical constraints. **ALL AI AGENTS MUST ADHERE TO THIS DOCUMENT.**

---

## 🧠 Core Vision

The Herbalife Distributor SaaS Platform is a multi-tenant, multi-agent ecosystem designed to provide a complete 360° virtual assistant for independent Herbalife distributors. It orchestrates specialized agents to handle complex business flows, from lead capture and customer service to sales and distributor onboarding.

*   **Frictionless Experience**: The platform must be intuitive, fast, and easy to use for both distributors and their prospects, minimizing cognitive load and manual steps.
*   **Orchestration**: A robust state management system to handle conversations and business processes.
*   **Intelligence**: A hybrid approach combining RAG (Retrieval-Augmented Generation) for knowledge-intensive tasks, and multiple LLMs for flexibility and performance.
*   **Goal**: Full automation of lead qualification, customer support, sales, and scheduling, with a seamless experience for both distributors and their clients.

---

## 📜 Agentic Engineering Principles

All development must follow the principles outlined in the **AGENTIC INFRASTRUCTURE & SOCIOECONOMIC MANAGEMENT (IAGS)** protocol (`SKILL_Agentic-Engineering-Protocol_IAGS.md`). The core objective is to maximize the "Total Integral of Value" by building a system that is efficient, resilient, and sovereign.

---

## 🛠 Technical Architecture (The "Stack")

### 1. Hybrid & Transitional Architecture (HTA)
The platform uses a hybrid architecture that leverages the power of centralized services while preparing for a decentralized future.

*   **Sovereign SQL Layer**: Use Relational SQL for indexing, but encrypt sensitive fields as blobs. Keys must be client-side (Zero-Knowledge).
*   **Training Readiness**: Separate private sovereign data (encrypted) from operational data (anonymized) to feed proprietary model training pipelines.
*   **Modular Intelligence**: Wrap AI calls in a `SkillAdapter` to remain agnostic to the specific LLM provider.

### 2. Data Layer
*   **Relational DB**: **Remote MySQL** (Primary).
*   **Vector DB**: **Pinecone** for document and conversation memory (`text-embedding-3-small`, 1536 dims).
*   **ORM**: SQLAlchemy 2.0+

### 3. Core Services
*   **Agent Orchestrator**: The "brain" that manages the state of conversations and agent interactions.
*   **RAG Service**: Handles vector database interactions for storing and retrieving information from documents and past conversations.
*   **LLM Service (SkillAdapter)**: A unified gateway for multiple LLM providers (OpenAI, Anthropic, Google Gemini).
*   **PDF Service**: Generates PDFs for wellness evaluations, reports, etc.

### 4. Integrations
*   **WhatsApp**: Custom Node.js service (`api-whatsapp`) for multi-tenant WhatsApp communication.
*   **Telegram**: `python-telegram-bot` for Telegram bot integration.
*   **Google**: Google Calendar & Gmail (via Google API) for scheduling and email.
*   **Email**: Generic SMTP support for sending emails.

---

## 🔒 Critical Rules & Constraints (Zero Tolerance)

### A. Data Sovereignty & Encryption
1.  **Cryptographic Integrity**: All personally identifiable information (PII) and sensitive customer data **MUST** be encrypted at the application level before being stored in the database.
2.  **Zero-Knowledge Principle**: The platform should not have access to the decryption keys for sensitive data. Keys should be managed by the user (distributor).
3.  **Anonymization**: Data used for training AI models **MUST** be anonymized to protect user privacy.

### B. Database Stability
1.  **Preventive Rollbacks**: You **MUST** execute `db.session.rollback()` at the absolute start of any tool function or service entry point to prevent "MySQL has gone away" errors.
2.  **No Lazy Loading in Loops**: Avoid accessing related database objects within loops to prevent excessive queries. Load necessary data into Python primitives before iterating.

### C. Environment & Security
*   **No Hardcoding**: All secrets must be stored in `.env` files.
*   **Critical Env Vars**: `OPENAI_API_KEY`, `PINECONE_API_KEY`, `DATABASE_URL`, `GOOGLE_CLIENT_ID`, `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`.
*   **Google Auth**: `GOOGLE_CREDENTIALS_JSON` (Base64 encoded) or path to `client_secret.json`.

### D. Business Logic Enforcements
1.  **Consensual Scheduling**: The Agent **CANNOT** book a calendar slot without explicit confirmation from the user.
2.  **Data Privacy**: All data for each distributor must be strictly isolated. Use a robust multi-tenancy strategy.
3.  **Lead Ownership**: Leads generated through a distributor's personalized link belong exclusively to that distributor.

### E. Offline-First Capabilities
*   The system should be designed to handle intermittent connectivity.
*   Frontend applications should cache data locally to provide a seamless user experience even when the connection to the backend is lost.
*   Agents should be able to queue actions and execute them when the connection is restored.

---

## 📋 Development Workflow

**Branching Strategy**:
1.  `main`: **PRODUCTION**. Read-only for AI.
2.  `dev`: **STAGING**. The target for all merges.
3.  `feature/[name]`: **WORKING**. Create this for every task.

**Commit Protocol**:
1.  **Create Artifact**: Create a task description (e.g., in `docs/tasks`).
2.  **Code**: Implement the changes.
3.  **Verify**: Run the code and any relevant tests.
4.  **Log**: Update `docs/development_log.md`.
5.  **Migration Path**: Every module must include a comment: `"Migration Path: How this SQL/Logic moves to a decentralized P2P state."`
6.  **Merge**: Create a pull request from `feature/[name]` to `dev`.

---

## ✅ Integration Status

| Component | Status | Details |
| :--- | :--- | :--- |
| **Auth** | 🟡 Planned | JWT + Google OAuth |
| **Database** | 🟡 Planned | Remote MySQL + Pinecone |
| **Orchestration** | 🟡 Planned | To be defined |
| **RAG** | 🟡 Planned | PDF/Docx uploads + Querying |
| **Scheduling** | 🟡 Planned | Google Calendar |
| **Payments** | 🟡 Planned | Subscription management |
| **CRM** | 🟡 Planned | Custom Customer/Lead Model |
| **WhatsApp** | 🟢 Ready | `api-whatsapp` service integrated |
| **Telegram** | 🟡 Planned | `python-telegram-bot` |
| **Email** | 🟡 Planned | SMTP integration |

---

## 📂 Project Structure Map

### 1. Backend Blueprints (`backend/routes/`)
*   **Auth**: Authentication and user management.
*   **Core**: Distributor settings, agent configuration, and channel integrations.
*   **Features**: RAG, chat, analytics, and wellness evaluations.
*   **External**: Webhooks for WhatsApp, Telegram, and other services.

### 2. Frontend (To be defined)
*   **Base**: Master layout and navigation.
*   **Auth**: Login, registration, and subscription pages.
*   **Dashboard**: Main dashboard with stats, CRM, and agent configuration.
*   **Public**: Wellness evaluation form.
