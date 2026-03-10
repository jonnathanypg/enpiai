"""
agent_orchestrator.py
Main agent orchestration using LangGraph with persistent memory.

This service replaces the manual message history management in agent_service.py
with LangGraph's built-in state management and checkpointing.
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, List
from flask import g

# LangChain / LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# Local imports
from services.agent_state import AgentState
from models.distributor import Distributor
from models.agent_config import AgentConfig
from models.conversation import Conversation

# Modular Logic Imports (Phase 8)
from skills import get_registry
from services.prompt_builder import SystemPromptBuilder

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    Multi-tenant LangGraph agent service with persistent memory.
    
    Features:
    - Automatic conversation memory via checkpointer
    - Modular Skill Injection (Phase 8)
    - Dynamic System Prompts (Phase 8)
    - Multi-agent support per distributor
    """
    
    _checkpointer = None
    
    @classmethod
    def get_checkpointer(cls):
        """Get checkpointer. Defaulting to MemorySaver for stability."""
        if cls._checkpointer is None:
            cls._checkpointer = MemorySaver()
            logger.info("LangGraph checkpointer: MemorySaver (volatile)")
        return cls._checkpointer
    
    def __init__(self, distributor: Distributor):
        self.distributor = distributor
        self.checkpointer = self.get_checkpointer()
        self.skill_registry = get_registry()

    def _get_llm(self, model_override: str = None):
        """Get LLM client with distributor credentials"""
        
        provider = self.distributor.llm_provider or 'openai'
        model = model_override or self.distributor.llm_model or 'gpt-5-nano'
        
        # Get API Key from api_keys JSON or fallback to env
        api_keys = self.distributor.api_keys or {}
        
        if provider == 'google':
             api_key = api_keys.get('google_api_key') or os.getenv('GOOGLE_API_KEY')
             return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=api_key,
                temperature=0.7,
                convert_system_message_to_human=True
            )
        else:
            api_key = api_keys.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
            return ChatOpenAI(
                model=model,
                api_key=api_key,
                temperature=1.0
            )
    
    def _resolve_skills(self, agent: AgentConfig, enabled_features: List[str]) -> List[Any]:
        """Dynamically resolve skills based on agent configuration."""
        active_skills = []
        
        # 1. Calendar / Scheduler
        if any(f in enabled_features for f in ['calendar_integration', 'calendar_scheduling', 'google_calendar']):
            active_skills.append(self.skill_registry.get_skill('scheduler'))

        # 2. RAG / Knowledge Base
        # Always enabled if distributor has documents? Or feature flag?
        # For now, rely on feature flag or default to enabled if RAG is ready
        if any(f in enabled_features for f in ['knowledge_base', 'rag']):
            active_skills.append(self.skill_registry.get_skill('knowledge_base'))

        # 3. CRM / Leads
        if any(f in enabled_features for f in ['crm_lookup', 'crm_integration', 'lead_capture']):
            active_skills.append(self.skill_registry.get_skill('crm'))

        # 4. Email / Communication
        if 'email_integration' in enabled_features:
            active_skills.append(self.skill_registry.get_skill('communication'))

        # 5. Wellness
        if 'wellness_evaluation' in enabled_features:
            active_skills.append(self.skill_registry.get_skill('wellness'))

        # 6. Cron / Follow-ups (Phase 9)
        if any(f in enabled_features for f in ['follow_ups', 'cron', 'scheduled_tasks']):
            active_skills.append(self.skill_registry.get_skill('cron'))

        return [s for s in active_skills if s is not None]

    def _build_system_prompt(self, agent: AgentConfig, state: AgentState, skills: List[Any]) -> str:
        """
        Build system prompt using the modular SystemPromptBuilder.
        """
        builder = SystemPromptBuilder(
            agent_config={
                'name': agent.name,
                'role': 'Asistente Virtual', # specific role can be in agent.config
                'tone': agent.tone.value if agent.tone else 'Profesional'
            },
            distributor=self.distributor
        )
        
        # Context Data
        context_data = {
            'current_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M (UTC)'),
            'contact_name': state.get('contact_name'),
            'channel': state.get('channel'),
            'flow_context': self._determine_flow_context(state.get('messages', [])),
            'agent_hints': state.get('agent_hints', ''),  # Phase 9: Sentiment/Identity
        }

        (
            builder
            .add_identity()
            .add_safety_rules()
            .add_skills(skills)
            .add_context(context_data)
        )
        
        return builder.build()

    def _determine_flow_context(self, messages: List) -> str:
        """Simple heuristic to determine flow context from recent messages."""
        if not messages:
            return "General"
            
        last_msg = messages[-1].content.lower() if hasattr(messages[-1], 'content') else ""
        
        if any(w in last_msg for w in ['cita', 'reunión', 'agendar', 'horario']):
            return "FLUJO_AGENDA"
        if any(w in last_msg for w in ['precio', 'costo', 'vendes', 'información', 'producto']):
            return "FLUJO_NEGOCIO"
            
        return "MANTÉN EL FLUJO"

    def _build_graph(self, agent: AgentConfig, skills: List[Any]):
        """Build LangGraph workflow using dynamic skills."""
        
        # Aggregate tools from all skills
        tools = []
        for skill in skills:
            tools.extend(skill.get_tools())

        llm = self._get_llm()
        llm_with_tools = llm.bind_tools(tools) if tools else llm
        
        # ========== Node: Agent Reasoning ==========
        def agent_node(state: AgentState) -> Dict[str, Any]:
            system_prompt = self._build_system_prompt(agent, state, skills)
            
            # Helper to manage history manually if checkpointer is not enough (it usually is)
            messages = list(state["messages"])
            all_messages = [SystemMessage(content=system_prompt)] + messages
            
            try:
                response = llm_with_tools.invoke(all_messages)
            except Exception as e:
                logger.error(f"LLM invoke error: {e}")
                response = AIMessage(content="Lo siento, tuve un problema técnico.")
            
            return {"messages": [response]}
        
        # ========== Node: Tool Execution ==========
        def tool_node(state: AgentState) -> Dict[str, Any]:
            last_message = state["messages"][-1]
            results = []
            
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                for tool_call in last_message.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    logger.info(f"[LANGGRAPH] Executing tool: {tool_name}")
                    
                    # Find tool execution function
                    tool_obj = next((t for t in tools if t.name == tool_name), None)
                    
                    if tool_obj:
                        try:
                            # Context Injection
                            g.current_company = self.distributor
                            result = tool_obj.invoke(tool_args)
                        except Exception as e:
                            logger.error(f"Tool error {tool_name}: {e}")
                            result = f"Error: {str(e)}"
                    else:
                        result = f"Tool {tool_name} not found"
                    
                    results.append(ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call["id"]
                    ))
            
            return {"messages": results}

        # ========== Routing ==========
        def should_continue(state: AgentState) -> str:
            last_message = state["messages"][-1]
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tools"
            return "end"

        workflow = StateGraph(AgentState)
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", tool_node)
        
        workflow.set_entry_point("agent")
        
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {"tools": "tools", "end": END}
        )
        workflow.add_edge("tools", "agent")
        
        return workflow.compile(checkpointer=self.checkpointer)

    def process_message(
        self, 
        conversation: Conversation, 
        user_message: str, 
        channel: str = "webchat", 
        thread_id: str = None
    ) -> Dict[str, Any]:
        """Process a message using the modular agent architecture (Phase 9 enhanced)."""
        
        try:
            from extensions import db
            db.session.rollback()
        except: pass

        # 1. Load Agent Config (respect priority — highest priority first)
        agent = AgentConfig.query.filter_by(
            distributor_id=self.distributor.id
        ).order_by(AgentConfig.priority.desc()).first()
        if not agent:
            return {"content": "System Error: No agent configuration.", "error": True}

        # 2. Resolve Enabled Features
        try:
            enabled_features = [f.name for f in agent.features.filter_by(is_enabled=True).all()]
        except:
            enabled_features = []

        # 3. Resolve Skills dynamically
        skills = self._resolve_skills(agent, enabled_features)
        
        # 4. Build Graph
        graph = self._build_graph(agent, skills)
        
        # 5. Thread ID
        if not thread_id:
            today_str = datetime.utcnow().strftime('%Y%m%d')
            thread_id = f"conv_{conversation.id}_{today_str}"

        # ========== Phase 9: Pre-Processing ==========
        
        # A. Sentiment Analysis
        sentiment_context = ""
        try:
            from services.sentiment_service import SentimentService
            sentiment = SentimentService(distributor=self.distributor)
            analysis = sentiment.analyze_text(user_message)
            if sentiment.should_escalate(analysis):
                sentiment_context = (
                    f"\n⚠️ ALERTA DE SENTIMIENTO: El usuario muestra frustración "
                    f"(score: {analysis['score']}, risk: escalación). "
                    f"Sé empático, ofrece soluciones concretas y pregunta si desea hablar con un humano."
                )
                logger.warning(f"[SENTIMENT] Escalation risk detected: {analysis}")
        except Exception as e:
            logger.debug(f"Sentiment analysis skipped: {e}")

        # B. Identity Resolution
        identity_context = ""
        try:
            from services.identity_resolver import IdentityResolver
            identity = IdentityResolver.resolve_from_conversation(conversation)
            if identity.get('found'):
                identity_context = f"\nContexto del contacto: {identity.get('context', '')}"
        except Exception as e:
            logger.debug(f"Identity resolution skipped: {e}")

        # ========== Invoke ==========
        enriched_message = user_message
        # Append context as invisible prefix for the agent (not shown to user)
        agent_hints = sentiment_context + identity_context

        initial_state = {
            "messages": [HumanMessage(content=enriched_message)],
            "company_id": self.distributor.id,
            "agent_id": agent.id,
            "conversation_id": conversation.id,
            "agent_name": agent.name,
            "channel": channel,
            "contact_name": conversation.participant_name or "Usuario",
            "enabled_features": enabled_features,
            "agent_hints": agent_hints,  # Available in state for prompt builder
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            result = graph.invoke(initial_state, config)
            
            # Extract final response
            for msg in reversed(result.get("messages", [])):
                if isinstance(msg, AIMessage):
                    return {"content": msg.content, "agent_name": agent.name}
            
            return {"content": "...", "agent_name": agent.name}
            
        except Exception as e:
            logger.error(f"[LANGGRAPH] Error: {e}")
            return {"content": "Lo siento, error interno.", "error": True}

def get_agent_orchestrator(distributor: Distributor) -> AgentOrchestrator:
    return AgentOrchestrator(distributor)


