# OnePunch - Multi-Agent System

**Copyright © 2025 WEBLIFETECH (Jonnathan Peña). All Rights Reserved.**

![OnePunch Banner](static/images/banner_placeholder.png)

OnePunch is a powerful, customizable multi-agent system designed to act as a 360° virtual department for businesses. By orchestrating specialized "Chefs" (Agents), it manages customer interactions, sales pipelines, scheduling, and RAG-based support through a unified interface.

---

## 🚀 Project Overview

OnePunch enables businesses to deploy AI agents that can:
*   **Communicate** via WhatsApp, Email, Voice, and SMS.
*   **Remember** context using Vector Memory (RAG with Pinecone).
*   **Execute Actions** like scheduling (Google Calendar), checking inventory (Google Sheets), and processing payments (PayPal).
*   **Personalize** interactions with specific tones, genders, and instructions.

### Core Philosophy
The system is built on the concept of **"Chefs"**—modulized agents with specific capabilities enabled via a simple checkbox interface. When a capability is checked (e.g., "Schedule Calls"), the agent gains access to the relevant tools and context.

---

## 🛠️ Tech Stack

*   **Backend Framework**: Python (Flask 3.0)
*   **Database**:
    *   **Relational**: MySQL (Hostinger Remote / SQLAlchemy)
    *   **Vector**: Pinecone (text-embedding-3-small)
*   **Authentication**: JWT Security
*   **Frontend**: HTML5, Vanilla CSS3 (Modern Glassmorphism), Vanilla JS
*   **AI/LLM**: Multi-provider support (OpenAI, Anthropic, Google Gemini)

---

## 📂 Architecture

```
OnePunch/
├── app.py                 # Application Factory & Entry Point
├── config.py              # Configuration & Environment
├── routes/                # API Endpoints (Blueprints)
├── models/                # Database Models (SQLAlchemy)
├── services/              # Business Logic (LLM, RAG, Agents)
├── templates/             # HTML Templates (Jinja2)
├── static/                # CSS, JS, Images
├── docs/                  # Documentation & Logs
└── migrations/            # Database Migrations (Alembic)
```

---

## ⚡ Development Status

**Current Phase: Integration & Scaling**

*   ✅ **Foundation**: Flask Structure, Auth System, Dashboard UI.
*   ✅ **Data Layer**: Remote MySQL for app data, Pinecone for RAG.
*   ✅ **Memory**: Vector search implemented with OpenAI Embeddings.
*   ✅ **Stability**: Production-ready architecture with robust ORM handling (MySQL persistent connections).
*   🚧 **Communications**: Twilio (WhatsApp/Voice) - *In Progress*.
*   📅 **Integrations**: Google Workspace, PayPal - *Planned*.

---

## 🔧 Installation & Setup

### Prerequisites
*   Python 3.10+
*   Virtualenv
*   Git

### Quick Start

1.  **Clone the repository**
    ```bash
    git clone https://github.com/NexusMetriks/onepunsh.git
    cd onepunch
    ```

2.  **Create Virtual Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**
    Copy `.env.example` to `.env` and fill in your keys:
    ```bash
    cp .env.example .env
    # Edit .env with your MySQL, Pinecone, and OpenAI keys
    ```

5.  **Run Migrations**
    ```bash
    flask db upgrade
    ```

6.  **Run Development Server**
    ```bash
    flask run --host=0.0.0.0 --port=5001
    ```
    Access the dashboard at `http://localhost:5001`.

---

## 🤝 Contribution Workflow

This project is proprietary. Development follows a strict feature-branch workflow monitored via `docs/development_log.md`.

1.  **Sync**: Always pull the latest `dev`.
2.  **Branch**: Create `feature/your-feature`.
3.  **Log**: Document progress in `docs/development_log.md`.
4.  **Merge**: Pull Request to `dev`.

See `GEMINI.md` for AI-specific guidelines.

---

**Developed by Jonnathan Peña for WEBLIFETECH.**
