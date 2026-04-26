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

*   **Backend**: Python (Flask 3.0) + LangGraph (AI Orchestration)
*   **Task Queue**: Celery + Redis
*   **Database**:
    *   **Relational**: MySQL (SQLAlchemy) with Application-Level Encryption (Fernet).
    *   **Vector**: Pinecone (Namespace-isolated RAG).
*   **Authentication**: JWT Security & Google OAuth.
*   **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, Shadcn UI.
*   **AI/LLM**: Multi-provider failover (OpenAI -> Anthropic -> Google Gemini).
*   **WhatsApp**: Custom Node.js Multi-tenant microservice (`api-whatsapp`).
*   **Internationalization**: Native support for EN, ES, PT (Backend & Frontend).

---

## 📂 Architecture

```
/
├── backend/               # Flask Application (API & Logic)
│   ├── routes/            # API Blueprints (Auth, CRM, RAG, etc.)
│   ├── models/            # SQLAlchemy Models with PII Encryption
│   ├── services/          # Core Business Logic & LangGraph Orchestrator
│   └── skills/            # Agentic Skills & Tools
├── frontend/              # Next.js Application (Dashboard & Public Forms)
├── api-whatsapp/          # Node.js Microservice for WhatsApp Connectivity
├── migrations/            # Database version control
└── docs/                  # Technical Guides and Analysis
```

---

## ⚡ Development Status

**Current Phase: Advanced Implementation / Pre-Production**

*   ✅ **Core Infrastructure**: Multi-tenant database, JWT Auth, and multi-provider LLM failover.
*   ✅ **Agent Orchestration**: LangGraph-based cyclic workflows with state persistence in Redis.
*   ✅ **WhatsApp Multi-Tenancy**: Dedicated gateway for asynchronous message processing.
*   ✅ **CRM & Wellness**: Unified contact view and health evaluation logic implemented.
*   ✅ **RAG System**: Automated document indexing and semantic search per distributor.
*   ✅ **I18n**: Subsystem active for EN, ES, and PT.
*   🚧 **UI Refinement**: Polishing dashboard components and reporting visualization.

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
