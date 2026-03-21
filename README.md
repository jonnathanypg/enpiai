# Herbalife Distributor SaaS Platform

**Copyright © 2026 WEBLIFETECH (Jonnathan Peña). All Rights Reserved.**


A powerful, all-in-one SaaS platform designed to empower independent Herbalife distributors. This platform provides a comprehensive suite of tools to manage and grow their business, from lead generation and customer relationship management to automated communication and team building.

---

## 🚀 Project Overview

This platform is a multi-tenant SaaS application that allows Herbalife distributors to subscribe to a monthly service and gain access to a powerful set of tools, including:

*   **AI-Powered Assistants:** Automated assistants that can handle customer inquiries via WhatsApp and Telegram.
*   **Wellness Evaluation System:** A customizable wellness evaluation form that distributors can share with prospects. The collected data is stored in a personalized CRM.
*   **CRM & Lead Management:** A dedicated dashboard for each distributor to manage their leads, track their progress, and view their history.
*   **Automated Email Marketing:** A system for sending automated emails to prospects and customers, with customizable templates and signatures.
*   **PDF Generation:** The ability to generate PDF documents for reports, evaluations, and other materials.
*   **Conversational Surveys:** Wellness evaluations can also be conducted through a conversational chat with the AI assistant.
*   **Google Calendar Integration:** Seamlessly schedule meetings and appointments with prospects and customers.
*   **Distributor-to-Agent Communication:** Distributors can interact with their own AI assistant via WhatsApp to get summaries, reports, and insights, and to give instructions.

### Core Philosophy
The platform is designed to be **frictionless** for both distributors and their prospects. The user experience is intuitive, fast, and easy to use, with a focus on simplicity and efficiency.

---

## 🛠️ Tech Stack

*   **Backend Framework**: Python (Flask 3.0)
*   **Database**:
    *   **Relational**: MySQL (SQLAlchemy)
    *   **Vector**: Pinecone (for RAG and contextual memory)
*   **Authentication**: JWT Security & Google OAuth
*   **Frontend**: Modern, responsive UI (details to be defined)
*   **AI/LLM**: Multi-provider support (OpenAI, Anthropic, Google Gemini)
*   **WhatsApp Integration**: Custom Node.js service (`api-whatsapp`)
*   **Telegram Integration**: Python Telegram Bot
*   **Email**: SMTP integration
*   **Calendar**: Google Calendar API

---

## 📂 Architecture

```
/
├── backend/               # Main Flask application
│   ├── app.py             # Entry Point
│   ├── celery_app.py      # Celery Configuration
│   ├── routes/            # API Blueprints
│   ├── models/            # Database Models
│   ├── services/          # Business Logic
│   └── skills/            # Agentic Skills
├── frontend/              # Next.js Application
├── whatsapp-gateway/      # Node.js WhatsApp Service
├── docs/                  # Documentation
└── migrations/            # Database Migrations
```

---

## ⚡ Development Status

**Current Phase: Project Scaffolding & Documentation**

*   ✅ **Project Initialization**: Basic folder structure created.
*   ✅ **Reference Analysis**: `OnePunch` and `openclaw` projects analyzed for best practices.
*   🚧 **Documentation**: `README.md`, `GEMINI.md`, `AGENTS.md`, and development manual in progress.

---

## 🔧 Installation & Setup

### Prerequisites
*   Python 3.10+
*   Node.js 18+
*   Virtualenv
*   Git

### Quick Start (Automated)

1.  **Clone the repository**
    ```bash
    git clone <your-repo-url>
    cd enpiai
    ```

2.  **Environment Variables**
    -   Configure `.env` in `backend/`, `frontend/`, and `whatsapp-gateway/`.

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

5.  **Terminal 5 (WhatsApp Gateway)**
    ```bash
    cd whatsapp-gateway
    npx @agenticnucleus/whatsapp-multitenant
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
