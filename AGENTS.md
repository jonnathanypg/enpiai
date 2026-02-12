# AGENTS.md

**Application name:** Herbalife Distributor SaaS Platform

This document outlines the multi-agent architecture for the platform, following the **AGENTIC INFRASTRUCTURE & SOCIOECONOMIC MANAGEMENT (IAGS)** protocol. The system is designed around a core set of specialized agents, each acting as an "Agentic Architect" with a distinct role and a set of capabilities (or "skills").

---

## 1. Agentic Architecture & Orchestration

The platform's intelligence is managed by a central **Agent Orchestrator**. This component is responsible for:

1.  **State Management:** Maintaining the state of all conversations and business processes.
2.  **Intent Recognition:** Determining the user's intent and the goal of their request.
3.  **Skill-Based Routing:** Routing tasks to the appropriate agent and skill based on the recognized intent.
4.  **Response Synthesis:** Composing the final response to the user based on the output of the skills.

All AI-powered skills are accessed through a `SkillAdapter`, an abstraction layer that allows for swapping the underlying LLM provider without changing the core application logic. This ensures modularity and future-proofs the system against changes in the AI landscape.

---

## 2. Agent Roles & Skills

### 2.1. Prospect/Customer Agent

This agent is the primary point of contact for new leads and existing customers. It is designed to be friendly, helpful, and knowledgeable, embodying the "frictionless" principle of the platform.

**Core Responsibilities:**

*   Answer product-related questions.
*   Conduct wellness evaluations (via web form or conversational chat).
*   Qualify leads (customer vs. potential distributor).
*   Schedule appointments with the distributor.
*   Handle basic customer service inquiries.

**Skills:**

*   **`knowledge_base_search`**: Searches the RAG vector store for information about products, ingredients, and business opportunities.
*   **`wellness_evaluation`**: Guides a user through the wellness evaluation, either conversationally or by providing a link to the web form.
*   **`lead_qualification`**: Asks targeted questions to determine if a prospect is interested in products or the business.
*   **`calendar_scheduling`**: Integrates with the distributor's Google Calendar to find available slots and book appointments.
*   **`crm_lookup`**: Retrieves information about existing customers from the CRM.

***Migration Path:** The logic for this agent, including its state and skills, should be designed to be portable to a decentralized P2P network where the agent runs on a user-controlled node.*

### 2.2. Distributor Agent

This agent acts as a personal assistant to the Herbalife distributor, providing them with real-time insights and tools to manage their business directly from their WhatsApp.

**Core Responsibilities:**

*   Provide daily/weekly summaries of new leads and their status.
*   Answer distributor questions about their prospects.
*   Send personalized messages to leads on behalf of the distributor.
*   Provide business tips and best practices.
*   Manage the distributor's calendar and appointments.

**Skills:**

*   **`crm_reporting`**: Generates reports and summaries from the CRM data (e.g., "how many new leads this week?").
*   **`prospect_messaging`**: Sends pre-defined or custom messages to specific leads or groups of leads.
*   **`data_analysis`**: Provides insights and analysis on lead conversion rates, popular products, etc.
*   **`content_generation`**: Helps the distributor draft social media posts, email newsletters, or other content.
*   **`distributor_calendar_management`**: Allows the distributor to view, schedule, and cancel appointments via WhatsApp.

***Migration Path:** The logic for this agent, including its state and skills, should be designed to be portable to a decentralized P2P network where the agent runs on a user-controlled node.*

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
