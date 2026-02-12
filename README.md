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

The project will be structured as a modular Flask application, with a separate Node.js service for WhatsApp integration.

```
/
├── api-whatsapp/          # Pre-built WhatsApp service
├── backend/               # Main Flask application
│   ├── app.py             # Application Factory & Entry Point
│   ├── config.py          # Configuration & Environment
│   ├── routes/            # API Endpoints (Blueprints)
│   ├── models/            # Database Models (SQLAlchemy)
│   ├── services/          # Business Logic (LLM, RAG, Agents)
│   ├── templates/         # HTML Templates (Jinja2)
│   └── static/            # CSS, JS, Images
├── docs/                  # Documentation
└── migrations/            # Database Migrations (Alembic)
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

### Quick Start

1.  **Clone the repository**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Setup Backend (Python)**
    ```bash
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    # Edit .env with your database, API keys, etc.
    flask db upgrade
    flask run
    ```

3.  **Setup WhatsApp API (Node.js)**
    ```bash
    cd ../api-whatsapp
    npm install
    cp .env.example .env
    # Edit .env with your WhatsApp API settings
    npm start
    ```

---

## 🤝 Contribution Workflow

This project follows a strict feature-branch workflow.

1.  **Sync**: Always pull the latest `dev`.
2.  **Branch**: Create `feature/your-feature`.
3.  **Log**: Document progress in `docs/development_log.md`.
4.  **Merge**: Pull Request to `dev`.

See `GEMINI.md` for AI-specific guidelines.

---

**Developed by Jonnathan Peña for WEBLIFETECH.**
