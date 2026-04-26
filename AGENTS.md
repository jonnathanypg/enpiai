# AGENTS.md

**Application name:** Herbalife Distributor SaaS Platform

This document outlines the multi-agent architecture for the platform, following the **AGENTIC INFRASTRUCTURE & SOCIOECONOMIC MANAGEMENT (IAGS)** protocol. The system is designed around a core set of specialized agents, each acting as an "Agentic Architect" with a distinct role and a set of capabilities (or "skills").

---

## 1. Agentic Architecture & Orchestration

The platform's intelligence is managed by a central **Agent Orchestrator**. This component is responsible for:

1.  **State Management:** Maintaining the state of all conversations and business processes using `AgentState` (TypedDict).
2.  **Intent Recognition:** Determining the user's intent and the goal of their request via LLM reasoning.
3.  **Skill-Based Routing:** Routing tasks to the appropriate tool (skill) using LangGraph's tool-calling logic.
4.  **Response Synthesis:** Composing the final response to the user based on the output of the skills and the distributor's persona.

All AI-powered skills are accessed through a `SkillAdapter`, an abstraction layer that allows for swapping the underlying LLM provider without changing the core application logic. This ensures modularity and future-proofs the system against changes in the AI landscape.

---

## 2. Agent Roles & Skills

### 2.1. Prospect/Customer Agent

This agent is the primary point of contact for new leads and existing customers. It is designed to be friendly, helpful, and knowledgeable, embodying the "frictionless" principle of the platform.

**Core Responsibilities:**

*   Answer product-related questions.
*   Conduct wellness evaluations (via web form or conversational chat).
*   Qualify leads (customer vs. lead identification).
*   Schedule appointments with the distributor using Google Calendar.
*   Handle basic customer service inquiries.

**Skills (Implemented Tools):**

*   **`consult_knowledge_base`**: Semantic search in the RAG vector store for information about products, ingredients, and the business.
*   **`wellness_evaluation_link`**: Provides the link to the public wellness evaluation form for health assessments.
*   **`lookup_customer`**: Searches for existing customers/leads by email to verify identity and status.
*   **`register_lead`**: Capture and registration of new prospects in the CRM with automated status assignment.
*   **`check_availability`**: Consults the distributor's Google Calendar for available time slots.
*   **`schedule_appointment`**: Creates events in Google Calendar and records them in the local database.
*   **`send_email`**: Sends formatted emails to users for follow-ups, reports, or confirmations.

***Migration Path:** The logic for this agent, including its state and skills, is designed via LangGraph to be portable to a decentralized P2P network where the agent runs on a user-controlled node.*

### 2.2. Distributor Agent

This agent acts as a personal assistant to the distributor, providing real-time insights and management tools directly via WhatsApp.

**Core Responsibilities:**

*   Provide daily/weekly summaries of new leads.
*   Answer questions about prospect status and history.
*   Manage the distributor's calendar.
*   Coordinate follow-up tasks and notifications.

**Skills:**

*   **`crm_reporting`**: Analysis of CRM data for conversion rates and lead status.
*   **`prospect_messaging`**: Orchestrated messaging via the WhatsApp Gateway.
*   **`calendar_management`**: High-level CRUD operations on the distributor's agenda.

***Migration Path:** This agent's architecture leverages the same LangGraph persistence as the Customer Agent, ensuring sovereign state management.*

---

## 3. Agent Configuration & Customization

Each distributor will have their own instance of these agents, which they can configure and customize from their dashboard.

**Customization Options:**

*   **Agent Persona:** Distributors can choose a name, gender, and tone for their customer-facing agent.
*   **Personalized Responses:** Distributors can customize the responses for common questions and scenarios.
*   **Skill Activation:** Distributors can enable or disable certain skills for their agents.
*   **Business Information:** Distributors can provide specific information about their business hours, contact information, and personal story, which the agent will use in its interactions.

---

This agent architecture provides a powerful and flexible foundation for the Herbalife Distributor SaaS Platform, enabling a high degree of automation and personalization for each distributor, while adhering to the principles of agentic engineering for a robust and future-proof system.
