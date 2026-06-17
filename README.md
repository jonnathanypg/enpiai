# Herbalife Distributor SaaS Platform

**Copyright © 2026 WEBLIFETECH (Jonnathan Peña). All Rights Reserved.**


A powerful, all-in-one SaaS platform designed to empower independent Herbalife distributors. This platform provides a comprehensive suite of tools to manage and grow their business, from lead generation and customer relationship management to automated communication and team building.

---

## 🚀 Project Overview

This platform is a multi-tenant SaaS application that allows distributors to subscribe to a monthly service and gain access to a powerful set of tools, including:

*   **AI-Powered Assistants:** Automated assistants orchestrated via **LangGraph** that handle customer inquiries via WhatsApp and Telegram.
*   **Wellness Evaluation System:** A customizable wellness evaluation system (conversational and web-form based) that stores data in a personalized CRM.
*   **CRM & Lead Management:** Unified 360° contact view for managing leads and customers with interaction timelines.
*   **Automated Email Marketing:** System for notifications, lead follow-ups, and reports.
*   **RAG (Retrieval-Augmented Generation):** Knowledge base management using **Pinecone** for company-specific documents.
*   **Google Calendar Integration:** Consensual bi-directional scheduling.
*   **Dashboards:** Modern Next.js metrics and management panels for distributors and administrators.

### Core Philosophy
The platform is designed to be **frictionless** for both distributors and their prospects. The user experience is intuitive, fast, and easy to use, with a focus on simplicity and efficiency.

---

## 🛠️ Tech Stack

*   **Backend**: Python (FastAPI + Flask Gateway) + LangGraph (AI Orchestration)
*   **Task Queue**: Celery + Redis
*   **Database**:
    *   **Relational**: MySQL (SQLAlchemy) with Application-Level Encryption (Fernet).
    *   **Vector**: Pinecone (Namespace-isolated RAG).
*   **Authentication**: JWT Security & Google OAuth.
*   **Payments**: PayPal Smart Buttons (with Guest Checkout & Direct Verification).
*   **Frontend**: Next.js 15 (React 19), TypeScript, Tailwind CSS, Shadcn UI.
*   **AI/LLM**: Multi-provider failover (OpenAI -> Google Gemini -> Anthropic).
*   **WhatsApp**: Custom Node.js Multi-tenant microservice (`api-whatsapp`).
*   **Internationalization**: Native support for EN, ES, PT (Backend & Frontend).

---

## 📂 Architecture

```
/
├── backend/               # FastAPI Gateway + Flask Logic
│   ├── routes/            # API Blueprints (Auth, CRM, RAG, Billing, etc.)
│   ├── models/            # SQLAlchemy Models with PII Encryption
│   ├── services/          # Core Business Logic & LangGraph Orchestrator
│   └── skills/            # Agentic Skills & Tools
├── frontend/              # Next.js Application (Dashboard & Public Forms)
├── api-whatsapp/          # Node.js Microservice for WhatsApp Connectivity
└── docs/                  # Technical Guides and Analysis
```

---

## ⚡ Development Status

**Current Phase: Production-Ready Core (Stabilization)**

*   ✅ **Core Infrastructure**: Multi-tenant database, JWT Auth, and multi-provider LLM failover.
*   ✅ **Agent Orchestration**: LangGraph-based cyclic workflows with state persistence in Redis.
*   ✅ **WhatsApp Multi-Tenancy**: Dedicated gateway for asynchronous message processing.
*   ✅ **Payments**: Integrated PayPal Smart Buttons (with Guest Checkout and instant server-side verification) for Subscriptions and Credit Blocks.
*   ✅ **CRM & Wellness**: Unified contact view and health evaluation logic implemented.
*   ✅ **RAG System**: Automated document indexing and semantic search per distributor.
*   ✅ **I18n & Themes**: Light/Dark theme support and EN/ES/PT i18n subsystem.
*   ✅ **Legal Disclaimers & Policies**: Complete public-facing Terms of Service, Privacy Policy, and Refund Policy routes implemented with dynamic i18n translations, specifying Herbalife non-affiliation, Fernet-encrypted PII/health data, and Google OAuth Limited Use rules.
*   ✅ **Channel Connections Polish**: Temporarily disabled Google Calendar and custom SMTP setup in dashboard settings, implementing a default mailing sender fallback via system SMTP (using `info@enpi.click` but showing distributor name dynamically as `"Distributor Name via EnpiAI"`).
*   ✅ **Analytics & Tracking**: Embedded Google Tag Manager (`GTM-54SSFHBZ`) tracking scripts inside Next.js root layout.
*   ✅ **Google Auth Resolution**: Fixed Google Sign-In "wrong audience" token verification mismatch between frontend and backend environment variables.
*   🚧 **Monitoring**: Fine-tuning remote MySQL latency handling for high traffic.

---

## 🔧 Installation & Setup

### Prerequisites
*   Python 3.10+
*   Node.js 18+
*   Redis 6+
*   MySQL 8.0+

### Quick Start (Automated)

1.  **Clone the repository**
    ```bash
    git clone <your-repo-url>
    cd enpiai
    ```

2.  **Environment Variables**
    -   Configure `.env` in `backend/`, `frontend/`, and `api-whatsapp/`.

3.  **Run everything**
    ```bash
    ./start-local.sh
    ```

### Manual Startup (Individual Terminals)

If you prefer to run services individually for debugging:

1.  **Terminal 1 (Redis)**
    ```bash
    redis-server
    ```

2.  **Terminal 2 (Backend)**
    ```bash
    cd backend
    source venv/bin/activate
    python3 app.py
    ```

3.  **Terminal 3 (Celery Worker)**
    ```bash
    cd backend
    source venv/bin/activate
    celery -A celery_app.celery worker --loglevel=info
    ```

4.  **Terminal 4 (Frontend)**
    ```bash
    cd frontend
    npm run dev
    ```

5.  **Terminal 5 (WhatsApp API)**
    ```bash
    cd api-whatsapp
    npm run build && npm start
    ```

---

## 🤝 Contribution Workflow

This project follows a strict feature-branch workflow.

1.  **Sync**: Always pull the latest `dev`.
2.  **Branch**: Create `feature/your-feature`.
3.  **Merge**: Pull Request to `dev`.

See `GEMINI.md` for AI-specific guidelines and `AGENTS.md` for information about the multi-agent architecture.

---

**Developed by Jonnathan Peña for WEBLIFETECH.**
