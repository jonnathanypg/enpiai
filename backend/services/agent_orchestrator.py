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
        """Get LLM client with distributor credentials and automated failover."""
        
        provider = self.distributor.llm_provider or 'openai'
        model = model_override or self.distributor.llm_model or 'gpt-5-nano'
        
        logger.info(f"[ORCHESTRATOR] Initializing LLM: provider={provider}, model={model}")
        
        # Get API Keys
        api_keys = self.distributor.api_keys or {}
        
        # 1. Resolve Keys
        openai_key = api_keys.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
        google_key = api_keys.get('google_api_key') or os.getenv('GOOGLE_AI_API_KEY')
        
        llms = []
        
        model_lower = model.lower()
        is_o_model = any(m in model_lower for m in ['o1', 'o3', 'gpt-5'])

        # Add OpenAI as primary
        if openai_key:
            kwargs = {
                "model": model,
                "api_key": openai_key,
            }
            
            if is_o_model:
                kwargs["max_completion_tokens"] = 4096 # Increased for reasoning
                kwargs["temperature"] = 1.0 # O-models prefer 1.0
            else:
                kwargs["max_tokens"] = 2048
                kwargs["temperature"] = 0.7

            llms.append(ChatOpenAI(**kwargs))

        # Add platform fallback (if distributor had their own key, fallback to platform key)
        platform_openai = os.getenv('OPENAI_API_KEY')
        if platform_openai and platform_openai != openai_key:
            llms.append(ChatOpenAI(
                model="gpt-5-nano",
                api_key=platform_openai,
                temperature=1.0,
                max_completion_tokens=4096
            ))

        # Add Google Gemini as second fallback if available
        if google_key:
            llms.append(ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=google_key,
                temperature=0.7,
                convert_system_message_to_human=True
            ))

        if not llms:
            raise RuntimeError("No LLM providers configured")

        if len(llms) == 1:
            return llms[0]
            
        return llms[0].with_fallbacks(llms[1:])
    
    def _resolve_skills(self, agent: AgentConfig, enabled_features: List[str]) -> List[Any]:
        """Dynamically resolve skills based on agent configuration.
        
        IMPORTANT: Feature names here must match the 'name' field in DEFAULT_FEATURES
        (agent_config.py). When adding new features, update BOTH places.
        """
        active_skills = []
        
        # 1. Calendar / Scheduler
        if any(f in enabled_features for f in [
            'calendar_scheduling', 'google_calendar',
            'calendar_integration',  # legacy alias
        ]):
            active_skills.append(self.skill_registry.get_skill('scheduler'))

        # 2. RAG / Knowledge Base
        if any(f in enabled_features for f in [
            'knowledge_base_search', 'rag_memory',
            'knowledge_base', 'rag',  # legacy aliases
        ]):
            active_skills.append(self.skill_registry.get_skill('knowledge_base'))

        # 3. CRM / Leads
        if any(f in enabled_features for f in [
            'crm_lookup', 'crm_reporting', 'lead_qualification', 'lead_capture',
            'crm_integration',  # legacy alias
        ]):
            active_skills.append(self.skill_registry.get_skill('crm'))

        # 4. Email / Communication
        if any(f in enabled_features for f in [
            'email', 'email_integration', 'prospect_messaging',
        ]):
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
        # Resolve best name: AgentConfig name or Distributor agent_name
        # If AgentConfig.name is generic (contains 'Asistente' but distributor.agent_name is specific), 
        # we might want to prioritize distributor.agent_name.
        # For now, we trust AgentConfig.name if it's set, but fallback to Distributor if needed.
        agent_name = agent.name
        if agent_name in ['Asistente', 'Asistente de Prospectos', 'Lead Assistant'] and self.distributor.agent_name:
            agent_name = self.distributor.agent_name

        builder = SystemPromptBuilder(
            agent_config={
                'name': agent_name,
                'role': 'Asistente Virtual', # specific role can be in agent.config
                'tone': agent.tone.value if agent.tone else 'Profesional'
            },
            distributor=self.distributor
        )
        
        # Context Data
        now = datetime.now()
        days_es = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
        day_name = days_es[now.weekday()]
        
        context_data = {
            'current_time': f"{now.strftime('%Y-%m-%d %H:%M:%S')} ({day_name})",
            'contact_name': state.get('contact_name'),
            'contact_phone': state.get('contact_phone'),
            'channel': state.get('channel'),
            'flow_context': self._determine_flow_context(state.get('messages', [])),
            'agent_hints': state.get('agent_hints', ''),  # Phase 9: Sentiment/Identity
            'is_anonymous': state.get('is_anonymous', False),
        }

        contact_type = state.get('contact_type', 'unknown')
        is_distributor = contact_type == 'distributor'
        
        if is_distributor:
            builder.add_distributor_persona()
        else:
            builder.add_identity()

        (
            builder
            .add_safety_rules()
            .add_skills(skills)
            .add_context(context_data)
            .add_final_reminder(is_distributor=is_distributor)
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
            logger.info(f"[LANGGRAPH] System prompt length: {len(system_prompt)}")
            
            # Helper to manage history manually if checkpointer is not enough (it usually is)
            messages = list(state["messages"])
            
            # Role mapping for O-models (gpt-5)
            # Use distributor config or default
            active_model = self.distributor.llm_model or 'gpt-5-nano'
            model_lower = active_model.lower()
            is_o_model = any(m in model_lower for m in ['o1', 'o3', 'gpt-5'])
            
            if is_o_model:
                # O-models often ignore 'system' but respect 'developer' or instructions in 'user'
                # We'll use a HumanMessage as a "Developer/Instruction" prefix if the model is picky
                # or just use SystemMessage and trust ChatOpenAI (which might map it to developer).
                # To be safe, we add a very clear final summary mandate to the prompt.
                summary_mandate = (
                    "\n\n## MANDATO FINAL DE RESPUESTA\n"
                    "Si has usado herramientas, DEBES resumir los resultados para el usuario. "
                    "NUNCA respondas con un mensaje vacío. Si no tienes nada más que decir, "
                    "confirma que has completado la tarea."
                )
                system_prompt += summary_mandate

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
                            ctx.current_company = self.distributor
                            ctx.current_conversation_id = state.get("conversation_id")
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
            from extensions import db, ctx
            db.session.rollback()
        except Exception as e:
            logger.debug(f"Preventive rollback failed (likely no active session): {e}")
        # 1. Load Agent Config (respect priority — highest priority first)
        agent = AgentConfig.query.filter_by(
            distributor_id=self.distributor.id
        ).order_by(AgentConfig.priority.desc()).first()
        if not agent:
            return {"content": "System Error: No agent configuration.", "error": True}

        # 2. Resolve Enabled Features
        try:
            enabled_features = [f.name for f in agent.features.filter_by(is_enabled=True).all()]
        except Exception as e:
            logger.error(f"Error resolving agent features: {e}")
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
        
        # A. Sentiment Analysis (fast keyword-based — no LLM call in hot path)
        sentiment_context = ""
        try:
            from services.sentiment_service import SentimentService
            sentiment = SentimentService(distributor=self.distributor)
            analysis = sentiment.fast_analyze(user_message)
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
        identity = {}
        is_distributor = False
        try:
            from services.identity_resolver import IdentityResolver

            # For messaging channels, resolve by phone/chat_id first so we can
            # detect when the sender IS the distributor themselves.
            if channel == 'whatsapp' and conversation.participant_id:
                identity = IdentityResolver.resolve_from_phone(
                    conversation.participant_id, self.distributor.id
                )
            elif channel == 'telegram' and conversation.participant_id:
                identity = IdentityResolver.resolve_from_telegram(
                    conversation.participant_id, self.distributor.id
                )
            else:
                identity = IdentityResolver.resolve_from_conversation(conversation)

            if identity.get('found'):
                # Short-circuit if AI responses are disabled for this contact
                if identity.get('is_ai_active', True) is False:
                    logger.info(f"[ORCHESTRATOR] AI responses disabled for {identity.get('type')}: {identity.get('id')}")
                    return {"content": None, "ignored": True, "reason": "ai_disabled"}

                if identity.get('type') == 'distributor':
                    is_distributor = True
                    identity_context = f"\n{identity.get('context', '')}"
                    logger.info(f"[ORCHESTRATOR] MASTER MODE activated for distributor {self.distributor.name}")
                else:
                    identity_context = f"\nContacto: {identity.get('context', '')}"
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
            "contact_name": conversation.participant_name, # Removed default "Usuario" to handle anonymous users better
            "contact_phone": conversation.participant_id,
            "contact_type": identity.get('type', 'unknown'),
            "enabled_features": enabled_features,
            "agent_hints": agent_hints,  # Available in state for prompt builder
            "is_anonymous": conversation.lead_id is None and not is_distributor,
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            logger.info(f"[LANGGRAPH] Invoking graph for thread: {thread_id}")
            result = graph.invoke(initial_state, config)
            
            # Detailed logging of results
            final_messages = result.get("messages", [])
            logger.info(f"[LANGGRAPH] Graph finished with {len(final_messages)} total messages")
            
            # Extract final response
            for msg in reversed(final_messages):
                if isinstance(msg, AIMessage):
                    content = msg.content
                    if not content and hasattr(msg, 'tool_calls') and msg.tool_calls:
                        logger.info(f"[LANGGRAPH] Last AIMessage has no content but has {len(msg.tool_calls)} tool calls")
                        continue
                    
                    logger.info(f"[LANGGRAPH] Final AIMessage found. Content length: {len(content) if content else 0}")
                    if content:
                        # Humanize response for prospects/leads (not distributor Master Mode)
                        if not is_distributor:
                            try:
                                from services.humanizer_service import ResponseHumanizer
                                content = ResponseHumanizer.humanize(
                                    planned_response=content,
                                    conversation=conversation,
                                    distributor=self.distributor
                                )
                            except Exception as humanize_err:
                                logger.error(f"Failed to humanize response: {humanize_err}")

                        logger.debug(f"[LANGGRAPH] Content preview: {content[:100]}...")
                        
                        # --- PROACTIVE FEATURE: Auto-Followup Scheduling ---
                        try:
                            # If this was a customer/lead (not master mode), schedule a 24h follow-up
                            if initial_state.get('contact_type') not in ['distributor'] and channel == 'whatsapp':
                                from services.cron_service import CronService
                                from models.scheduled_task import ScheduledTask
                                
                                # Check if a follow-up is already pending for this conversation
                                pending_task = ScheduledTask.query.filter_by(
                                    conversation_id=conversation.id,
                                    action='auto_followup',
                                    status='pending'
                                ).first()
                                
                                if not pending_task:
                                    # Use a more natural and subtle message
                                    name = initial_state.get('contact_name') or 'hola'
                                    if name.lower() == 'hola':
                                        followup_msg = "¿Pudiste revisar lo que te comenté? ¡Quedo atento por si tienes cualquier duda!"
                                    else:
                                        followup_msg = f"¡Hola {name}! ¿Cómo vas? Solo pasaba por aquí para ver si tuviste oportunidad de revisar la info. ¡Cualquier cosa me avisas!"
                                    
                                    CronService.schedule_followup(
                                        distributor_id=self.distributor.id,
                                        message=followup_msg,
                                        delay_minutes=1440, # 24 hours
                                        conversation_id=conversation.id,
                                        lead_id=conversation.lead_id,
                                        action='auto_followup',
                                        payload={
                                            'lead_phone': conversation.participant_id,
                                            'type': 'auto_followup_cascade',
                                            'step': 1
                                        }
                                    )
                                else:
                                    logger.debug(f"[LANGGRAPH] Skipping auto-followup schedule: already pending for conv {conversation.id}")
                        except Exception as followup_err:
                            logger.warning(f"Failed to schedule auto-followup: {followup_err}")

                    return {"content": content, "agent_name": agent.name}
            
            logger.warning("[LANGGRAPH] No AIMessage with content found in final state")
            return {"content": "...", "agent_name": agent.name}
            
        except Exception as e:
            logger.error(f"[LANGGRAPH] Error: {e}")
            return {"content": "Lo siento, error interno.", "error": True}

def get_agent_orchestrator(distributor: Distributor) -> AgentOrchestrator:
    return AgentOrchestrator(distributor)


