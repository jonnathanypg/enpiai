"""
LangGraph Agent Service
Main agent orchestration using LangGraph with persistent memory.

This service replaces the manual message history management in agent_service.py
with LangGraph's built-in state management and checkpointing.
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from flask import g

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from services.langgraph_state import AgentState
from services.langgraph_tools import get_tools_for_agent
from models.agent import Agent
from models.company import Company
from models.conversation import Conversation, Message, MessageRole


class LangGraphAgentService:
    """
    Multi-tenant LangGraph agent service with persistent memory.
    
    Features:
    - Automatic conversation memory via checkpointer
    - Tool calling with all OnePunch integrations
    - Multi-agent support per company
    - Channel-aware context
    """
    
    # Class-level checkpointer (shared across instances for memory persistence)
    _checkpointer = None
    
    @classmethod
    def get_checkpointer(cls):
        """Get or create the shared checkpointer"""
        if cls._checkpointer is None:
            # Use MemorySaver for now (in-memory, fast)
            # For production, use SqliteSaver or PostgresSaver
            cls._checkpointer = MemorySaver()
        return cls._checkpointer
    
    def __init__(self, company: Company):
        self.company = company
        self.checkpointer = self.get_checkpointer()
    
    def _get_llm(self, model_override: str = None):
        """Get LLM client with company credentials"""
        api_key = None
        if self.company and self.company.api_keys:
            api_key = self.company.api_keys.get('openai')
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        model = model_override or (self.company.llm_model if self.company else 'gpt-4o')
        
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=0.7
        )
    
    def _build_system_prompt(self, agent: Agent, state: AgentState) -> str:
        """Build system prompt from agent configuration"""
        
        # Internal context strings
        current_time = datetime.now()
        days_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        day_name = days_es[current_time.weekday()]
        
        # Location context (Hidden from greeting)
        location_context = ""
        if self.company.city and self.company.country:
            location_context = f"Tu ubicación física (CONTEXTO INTERNO): {self.company.city}, {self.company.country}."
        elif self.company.country:
            location_context = f"Tu ubicación física (CONTEXTO INTERNO): {self.company.country}."

        # Base identity block
        system_prompt_start = f"""
Eres {self.company.agent_name}, el asistente IA oficial de {self.company.name}.
Tu rol específico interno es: {agent.name}.
Tu personalidad es: {self.company.personality_prompt or agent.tone.value}.

INFORMACIÓN DE CONTEXTO (SOLO PARA TI):
- {location_context}
- Zona Horaria Empresa: {self.company.timezone or 'UTC'}.
- Fecha Actual: {day_name}, {current_time.strftime('%Y-%m-%d %H:%M')}.

REGLAS DE IDENTIDAD Y SALUDO:
1. TU NOMBRE PÚBLICO: Usa "{self.company.agent_name}".
2. SALUDO: "¡Hola! Soy {self.company.agent_name} de {self.company.name}..." + Ofrecer Ayuda. USALO SOLO SI ES EL PRIMER MENSAJE DE LA CONVERSACIÓN. Si ya estás hablando, NO vuelvas a saludar.
3. PROHIBIDO: NO digas "desde [Ciudad]" en el saludo.
4. TONO: {agent.tone.value}.

REGLAS UNIVERSALES DE COMUNICACIÓN:

USO DE CONOCIMIENTO DE EMPRESA (CRÍTICO):
- Si el usuario pregunta sobre la empresa (servicios, productos, tarifas, visión, misión):
  * EJECUTA `consult_knowledge_base(query)` EN ESTE MISMO TURNO.
  * PROHIBIDO decir "voy a consultar" sin ejecutar la herramienta.
- NUNCA inventes información. Si RAG no devuelve datos, ofrece agendar una reunion para resolver cualquier duda.

FORMATO DE RESPUESTA EN CHAT (webchat, whatsapp, telegram, sms):
- REGLA DE ORO: SÉ CONVERSACIONAL Y PROGRESIVO. TUS RESPUESTAS DEBEN SER CORTAS (MÁX 40 PALABRAS).
- PRIMERA RESPUESTA RAG: PROSESA la información recuperada y SOLO da una breve síntesis de 2 oraciones.
  * INCORRECTO: [Lista larga de servicios, misión, visión, etc.]
  * CORRECTO: "Somos WEBLIFETECH, especializados en automatización con IA y chatbots. ¿Te interesa saber cómo optimizamos ventas o atención al cliente?"
- PROHIBIDO volcar el contenido de RAG de golpe. Resume lo esencial y PREGUNTA para guiar.
- DEJA QUE EL USUARIO GUÍE. Solo profundiza con detalles específicos (máximo 2-3 bullets) si te lo piden explícitamente.
- Si RAG devuelve mucha info, NO la uses toda. Elige lo más relevante para una intro y descarta el resto hasta que te pregunten.

FORMATO EN EMAILS/PROPUESTAS:
- Aquí SÍ puedes ser detallado y completo.
- Usa Markdown: **negrita**, - bullets, ## encabezados.

REGLAS ANTI-REDUNDANCIA:
- NO pidas confirmación de datos que ya verificaste.
- NO hagas múltiples preguntas en un solo mensaje.
- Mantén respuestas CORTAS y DIRECTAS.
"""
        
        # Channel Context
        channel = state.get('channel', 'webchat')
        channel_info = f"\nCanal actual: {channel}"
        
        contact_info = ""
        if state.get('contact_name'):
            contact_info = f"\nHablas con: {state.get('contact_name')}"
        
        # Check enabled features for conditional prompts
        payment_instruction = ""
        enabled_features = [f.name for f in agent.features.filter_by(is_enabled=True).all()]
        
        # Check for agenda capability to create cross-reference
        calendar_enabled = any(f in enabled_features for f in ['calendar_integration', 'calendar', 'schedule_meeting'])
        agenda_exception = "EXCEPCIÓN CRÍTICA: SI EL USUARIO QUIERE AGENDAR, IGNORA ESTE PROTOCOLO Y USA EL DE AGENDAMIENTO." if calendar_enabled else ""
        
        if 'process_payment' in enabled_features:
            payment_instruction = f"""
=== PROTOCOLO OBLIGATORIO DE VERIFICACIÓN DE IDENTIDAD PARA PAGOS ===

REGLA #1: SIEMPRE PIDE EL CORREO PRIMERO. NO HAY EXCEPCIONES.

{agenda_exception}

PASO 1 - PEDIR CORREO (OBLIGATORIO):
- Cuando el usuario mencione pagar, abonar, o cualquier transacción (Y NO ESTÉ PIDIENDO AGENDAR), tu PRIMERA respuesta DEBE ser:
  "Para continuar con el pago, primero necesito verificar tu identidad. ¿Me podrías proporcionar tu correo electrónico?"
- NO pidas nombre, NO pidas cédula, NO pidas nada más. SOLO EL CORREO.

PASO 2 - BUSCAR EN BASE DE DATOS:
- Cuando el usuario te dé su correo, DEBES ejecutar la herramienta `lookup_customer` INMEDIATAMENTE.
- EXCEPCIÓN: Si YA ejecutaste lookup y el usuario ya confirmó sus datos (dijo "sí", "correcto", etc.), NO vuelvas a ejecutarlo. Pasa al siguiente paso.
- Si es la primera vez que te da el correo:
  * Ejecuta lookup_customer("correo@ejemplo.com")
  * NO respondas con texto antes de usar esta herramienta.
  * NO ofrezcas opciones.

PASO 3 - VALIDAR DATOS:
- Si el cliente EXISTE:
  * Lee los datos: Nombre y Número de Identificación (IdentNum).
  * Si tiene Nombre Y IdentNum: Responde "Te encontré registrado como [Nombre]. Tu número de identificación es [IdentNum]. ¿Son correctos estos datos?"
  * Si IdentNum es "None" o está vacío: "Tengo tu nombre como [Nombre], pero me falta tu número de cédula/identificación. ¿Me lo proporcionas?"
- Si el cliente NO EXISTE:
  * Responde: "No encontré tu correo en nuestros registros. Necesito registrarte. ¿Me das tu nombre completo y número de cédula?"

PASO 3.5 - GUARDAR CÉDULA (CUANDO EL USUARIO LA PROPORCIONA):
- Cuando el usuario te dé su número de cédula (ej: "0980976367"), DEBES ejecutar `register_customer` INMEDIATAMENTE.
- Usa los datos que ya tienes del lookup + la nueva cédula:
  * first_name: el nombre que encontraste
  * last_name: el apellido que encontraste
  * email: el correo que te dio antes
  * ident_number: la cédula que acaba de darte
- DESPUÉS de guardar: "¡Perfecto! He registrado tus datos." y CONTINÚA con el flujo activo.
- NO vuelvas a pedir el correo. Ya lo tienes.


PASO 4 - CONFIRMAR MONTO (MUY IMPORTANTE):
- REGLA DE ORO / FRESCURA DE DATOS:
  * Los datos de la solicitud ACTUAL invalidan cualquier dato anterior en el historial.
  * Si el usuario dice AHORA que quiere pagar $100, y hace 10 mensajes dijo $50, IGNORA los $50. El monto es $100.
  * Solo usa el monto que el usuario ha especificado en EL ÚLTIMO INTERCAMBIO sobre el pago.
- REGLA ABSOLUTA: NUNCA inventes ni cambies el monto que dijo el usuario.
- Si el usuario dijo "cien dólares", el monto es $100 USD. NO $50, NO $300. EXACTAMENTE $100.
- Si el usuario dijo "cincuenta dólares", el monto es $50 USD.
- Conversiones de palabras a números:
  * "uno" = 1, "diez" = 10, "veinte" = 20, "treinta" = 30, "cuarenta" = 40
  * "cincuenta" = 50, "sesenta" = 60, "setenta" = 70, "ochenta" = 80, "noventa" = 90
  * "cien" = 100, "doscientos" = 200, "trescientos" = 300, "quinientos" = 500, "mil" = 1000
- SIEMPRE confirma el monto EN NÚMEROS antes de crear el link:
  "Perfecto. Voy a generar un cobro de $[MONTO EXACTO EN NÚMEROS] USD por [CONCEPTO]. ¿Es correcto?"
- Si NO estás seguro del monto (el usuario escribió algo confuso), PREGUNTA:
  "No entendí el monto exacto. ¿Podrías decírmelo en números? Por ejemplo: 50, 100, 200..."

PASO 5 - GENERAR LINK:
- SOLO después de que el usuario confirme identidad Y monto, usa `paypal_create_order`.
- Cuando recibas la respuesta, USA el campo "formatted_link" directamente en tu respuesta.
- NO copies el URL completo. Usa el link formateado que dice "[👉 Click aquí para pagar](URL)".
- Presenta el link así: "Aquí está tu link de pago: [👉 Click aquí para pagar](URL)"

FASE DE CIERRE (POST-PAGO) - CRÍTICO:
- Una vez generado el link, EL FLUJO DE PAGO HA TERMINADO.
- PROHIBICIONES ABSOLUTAS EN FASE DE CIERRE:
  * NUNCA ejecutes `paypal_create_order` de nuevo.
  * El link de pago YA EXISTE en el historial de la conversación.
- Tu siguiente paso es ofrecer: "¿Quieres que te envíe los detalles de pago por correo?"

PROTOCOLO DE EMAIL POST-PAGO (OBLIGATORIO):
- SI EL USUARIO PIDE QUE LE ENVÍES ALGO POR CORREO (ej: "sí", "envíamelo", "mándamelo"):
  1. **SI el usuario pide información adicional** (servicios, tarifas, productos):
     a) EJECUTA `consult_knowledge_base(query="servicios tarifas productos")` INMEDIATAMENTE.
     b) ESPERA el resultado.
     c) LUEGO, **EJECUTA `send_email`** incluyendo:
        - Detalles del pago (monto, concepto, link de pago del historial).
        - La información de empresa obtenida de RAG.
     d) **PROHIBIDO**: Responder solo en el chat. DEBES ejecutar `send_email`.
  
  2. **Si NO pide información adicional**:
     - EJECUTA `send_email` solo con los detalles del pago.
  
  3. **Después de ejecutar `send_email` correctamente**:
     - Confirma: "Correo enviado a [email]. ¿Necesitas algo más?"
     - Despídete si el usuario está satisfecho.

**REGLA DE ORO**: Cuando el usuario pide "envíame por correo", SIEMPRE debes ejecutar `send_email`. NO es opcional. NO respondas solo en el chat.

RECUERDA: EL CORREO ES LO PRIMERO. SIEMPRE. Y NUNCA CAMBIES EL MONTO DEL USUARIO.
""".strip()

        calendar_instruction = ""
        # Calendar Protocol (Conditioned on variable calculated above)
        if calendar_enabled:
            # Get company timezone info dynamically
            company_tz = self.company.timezone or 'UTC'
            company_location = ""
            if self.company.city and self.company.country:
                company_location = f"{self.company.city}, {self.company.country}"
            elif self.company.country:
                company_location = self.company.country
            else:
                company_location = "no especificada"
            
            calendar_instruction = f"""
=== PROTOCOLO DE AGENDAMIENTO ===

ZONA EMPRESA (INTERNO): {company_tz} ({company_location})

INFORMACIÓN REQUERIDA:
1. Fecha y hora
2. Ciudad/País (OBLIGATORIO para Timezone)
3. Motivo
4. Correo
5. Nombre (SOLO si no existe en BD)

REGLA DE ORO DE INTERACCIÓN:
1. SI EL USUARIO SALUDA: Saluda brevemente, preséntate y ofrece opciones. NO ASUMAS QUE QUIERE AGENDAR.
2. SI EL USUARIO ELIGE AGENDAR: Inicia el FLUJO DE AGENDAMIENTO.
3. SI EL USUARIO ELIGE PAGAR: Inicia el protocolo de pago.

FLUJO DE AGENDAMIENTO (SIN REDUNDANCIAS):
1. Pregunta día y hora deseados.
2. Pide correo y ejecuta `lookup_customer(email)` INTERNAMENTE.
   - Si existe: Usa su nombre y ciudad (NO re-confirmes datos ya obtenidos).
   - Si no existe: Pide nombre y ciudad.
3. Pide motivo de la reunión (breve, sin pedir confirmaciones extras).
4. Verifica disponibilidad con `check_availability(date, timezone, preferred_time)`.
   - Si la hora preferida NO está disponible:
     * Presenta las opciones al usuario (ej: "13:00 no está disponible. Opciones cercanas: 11:30, 12:30, 13:30, 14:30. ¿Cuál prefieres?").
     * ESPERA LA RESPUESTA DEL USUARIO. NO PROCEDAS HASTA QUE EL USUARIO ELIJA.
     * PROHIBIDO: Agendar automáticamente en cualquier horario sin que el usuario lo confirme explícitamente.
   - Si la hora preferida SÍ está disponible (✅): Procede al paso 5.
5. Cuando el usuario CONFIRME un horario específico O cuando `check_availability` devuelva "✅ disponible":
   - EJECUTA `schedule_appointment` INMEDIATAMENTE.
   - USA EL NOMBRE que obtuviste en el paso 2 (`lookup_customer`).
   - PROHIBIDO PREGUNTAR: "¿quieres que reserve?", "¿confirmas?", "¿procedemos?", "¿te parece bien?".
   - NO ESPERES confirmación adicional. El usuario YA eligió el horario. AGENDA AHORA.

FASE DE CIERRE (POST-AGENDAMIENTO) - CRÍTICO:
- Una vez que `schedule_appointment` devuelva "Cita agendada", EL AGENDAMIENTO HA TERMINADO.
- PROHIBICIONES ABSOLUTAS EN FASE DE CIERRE:
  * NUNCA ejecutes `check_availability` de nuevo.
  * NUNCA ejecutes `schedule_appointment` de nuevo.
  * La cita YA EXISTE. El link de Meet YA FUE generado.
- Tu siguiente y ÚNICO paso es ofrecer: "¿Quieres que te envíe un resumen por correo?"
- SI EL USUARIO DICE "SÍ/OK/ENVÍAME" EN ESTA FASE:
  1. SI te pide info de empresa: PRIMERO ejecuta `consult_knowledge_base(query="servicios tarifas productos")` y ESPERA el resultado.
  2. Luego ejecuta `send_email` incluyendo:
     - El resumen de la cita (fecha, hora, tema, link Meet del historial).
     - La información de empresa que obtuviste de RAG (NO inventes, NO pongas placeholders).
  3. Si RAG no devuelve info útil, solo envía el resumen de la cita sin inventar.
  4. Despídete.

REGLAS ESPECÍFICAS DE AGENDAMIENTO:
- NO preguntes "¿quieres que reserve?" si el usuario ya eligió un horario.
- NO pidas confirmación de datos que ya verificaste (nombre, correo).
""".strip()
        
        # Build dynamic protocol list for instructions
        active_protocols = []
        if 'process_payment' in enabled_features:
            active_protocols.append("Pagos")
        if calendar_enabled:
            active_protocols.append("Agendamiento")
        
        protocols_text = " o ".join(active_protocols) if active_protocols else "Ninguno"
        
        # Flow context rules (only if both protocols could be active)
        flow_context_rules = ""
        if 'process_payment' in enabled_features and calendar_enabled:
            flow_context_rules = """
=== REGLAS DE CONTEXTO DE FLUJO (MÁXIMA PRIORIDAD) ===

DETECCIÓN DE FLUJO:
- FLUJO_PAGO: Usuario menciona "pagar", "abonar", "cobro", "factura", "transferencia", "saldo", "deuda".
- FLUJO_AGENDA: Usuario menciona "agendar", "cita", "reunión", "meeting", "horario", "calendario", "reservar".
- FLUJO_NEUTRAL: Saludos, preguntas generales, soporte.

REGLAS DE BLOQUEO:
1. Una vez detectado un flujo, MANTENTE EN ÉL hasta completarlo.
2. Después de `lookup_customer`:
   - Si estás en FLUJO_PAGO → Tu siguiente paso es sobre el PAGO (confirmar monto, generar link).
   - Si estás en FLUJO_AGENDA → Tu siguiente paso es sobre la AGENDA (ciudad, motivo, disponibilidad).
3. NUNCA cambies de flujo sin que el usuario lo pida EXPLÍCITAMENTE.

PROHIBICIONES ESTRICTAS:
- En FLUJO_PAGO: NO preguntes "¿para qué día?", "¿cuál es el motivo?", "¿verifico disponibilidad?".
- En FLUJO_AGENDA: NO preguntes "¿cuánto deseas pagar?", "¿genero link de pago?", "¿confirmo el monto?".

CAMBIO DE FLUJO:
- Solo si el usuario dice "mejor quiero [otra cosa]", confirma el cambio antes de proceder.
"""
        
        full_prompt = f"""
{system_prompt_start}

{channel_info}
{contact_info}

{flow_context_rules}

PROTOCOLOS ACTIVOS ({protocols_text}):
{payment_instruction}
{calendar_instruction}

INSTRUCCIONES GENERALES:
1. SI existe un Protocolo activo en curso, SÍGUELO sin desviarte.
2. Si el usuario solo saluda, preséntate y ofrece las opciones disponibles.
3. NUNCA inventes información sobre la empresa - usa `consult_knowledge_base` primero.
4. ACTUALIZACIÓN DE DATOS: Si el usuario proporciona info nueva, usa `register_customer` para guardarla.
5. Después de completar un flujo, ofrece ayuda adicional UNA sola vez.
6. CONTINUIDAD: Una vez terminado un flujo (después de despedirte o enviar correo), quedas LIBRE para iniciar otro protocolo si el usuario lo pide (ej: agendar después de pagar).
""".strip()
        
        return full_prompt
    
    def _build_graph(self, agent: Agent, tools: List):
        """Build LangGraph workflow for agent"""
        llm = self._get_llm()
        llm_with_tools = llm.bind_tools(tools) if tools else llm
        
        # ========== Node: Agent Reasoning ==========
        def agent_node(state: AgentState) -> Dict[str, Any]:
            """Main agent reasoning node"""
            # Build system prompt
            system = self._build_system_prompt(agent, state)
            
            # Prepare messages with system prompt
            all_messages = [SystemMessage(content=system)] + list(state["messages"])
            
            # Call LLM
            response = llm_with_tools.invoke(all_messages)
            
            return {"messages": [response]}
        
        # ========== Node: Tool Execution ==========
        def tool_node(state: AgentState) -> Dict[str, Any]:
            """Execute tool calls from the agent"""
            last_message = state["messages"][-1]
            results = []
            
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                for tool_call in last_message.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    print(f"[LANGGRAPH] Executing tool: {tool_name} with args: {tool_args}")
                    
                    # Find the tool function
                    tool_fn = next((t for t in tools if t.name == tool_name), None)
                    
                    if tool_fn:
                        try:
                            # Set company context in Flask g for tools
                            g.current_company = self.company
                            
                            # Execute tool
                            result = tool_fn.invoke(tool_args)
                            print(f"[LANGGRAPH] Tool result: {result[:200] if len(str(result)) > 200 else result}")
                        except Exception as e:
                            result = f"Error executing {tool_name}: {str(e)}"
                            print(f"[LANGGRAPH] Tool error: {result}")
                    else:
                        result = f"Tool {tool_name} not found"
                    
                    results.append(ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call["id"]
                    ))
            
            return {"messages": results}
        
        # ========== Conditional: Continue or End ==========
        def should_continue(state: AgentState) -> str:
            """Decide whether to continue to tools or end"""
            last_message = state["messages"][-1]
            
            # If the last message has tool calls, execute them
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tools"
            
            # Otherwise, we're done
            return "end"
        
        # ========== Build Graph ==========
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", tool_node)
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add conditional edge from agent
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                "end": END
            }
        )
        
        # Tools always loop back to agent
        workflow.add_edge("tools", "agent")
        
        # Compile with checkpointer for memory
        return workflow.compile(checkpointer=self.checkpointer)
    
    def _select_agent(self, message: str) -> Optional[Agent]:
        """Select best agent for the message (or return default)"""
        agents = Agent.query.filter_by(
            company_id=self.company.id,
            is_active=True
        ).all()
        
        if not agents:
            return None
        
        if len(agents) == 1:
            return agents[0]
        
        # TODO: Implement smart routing based on message content
        # For now, return first active agent
        return agents[0]
    
    def process_message(
        self,
        conversation: Conversation,
        user_message: str,
        agent: Agent = None,
        channel: str = "webchat",
        thread_id: str = None
    ) -> Dict[str, Any]:
        """
        Process a message using LangGraph with automatic memory.
        
        Args:
            conversation: Conversation model instance
            user_message: The user's message
            agent: Specific agent to use (or auto-select)
            channel: Channel type (telegram, whatsapp, webchat, etc.)
            thread_id: Optional specific thread ID for persistence (overrides default)
            
        Returns:
            Dict with response content, tool calls, etc.
        """
        # Preventive rollback to clear any stale MySQL connections
        # This fixes "MySQL server has gone away" errors after inactivity
        try:
            from extensions import db
            db.session.rollback()
        except Exception:
            pass  # Ignore if no transaction to rollback
        
        print(f"\n[LANGGRAPH] Processing message for conversation {conversation.id}")
        
        # Select agent if not provided
        if not agent:
            agent = self._select_agent(user_message)
        
        if not agent:
            return {
                "content": "I'm sorry, no agents are available. Please contact support.",
                "error": True
            }
        
        print(f"[LANGGRAPH] Using agent: {agent.name}")
        
        # CRITICAL: Extract feature names BEFORE rollback to avoid lazy-load failures
        # These are simple Python strings that won't trigger DB queries later
        try:
            enabled_feature_names = [f.name for f in agent.features.filter_by(is_enabled=True).all()]
        except Exception as e:
            print(f"[LANGGRAPH] Warning: Could not load agent features: {e}")
            enabled_feature_names = []
        
        try:
            from extensions import db
            # Rollback to clear any stale connections
            db.session.rollback()
        except Exception as e:
            print(f"[LANGGRAPH] Warning during rollback: {e}")
            pass
        
        # Get tools for this agent (using pre-loaded feature names, no DB access)
        tools = get_tools_for_agent(agent, self.company, enabled_features=enabled_feature_names)
        print(f"[LANGGRAPH] Available tools: {[t.name for t in tools]}")
        
        # Build graph
        graph = self._build_graph(agent, tools)
        
        # Thread ID for memory persistence
        # Priority 1: Provided thread_id (e.g. from Web Widget Session)
        # Priority 2: Daily Session for Persistent Channels (WhatsApp/Telegram)
        # This ensures they keep context during the day but start fresh next day
        if not thread_id:
            today_str = datetime.utcnow().strftime('%Y%m%d')
            thread_id = f"conv_{conversation.id}_{today_str}"
            
        print(f"[LANGGRAPH] Using thread_id: {thread_id}")
        
        # Build initial state
        # Hydrate history from persistence (MySQL) to ensure context across restarts
        history_messages = []
        
        try:
            # Only load messages from the last 24 hours to prevent old context pollution
            time_window = datetime.utcnow() - timedelta(hours=24)
            
            db_messages = Message.query.filter(
                Message.conversation_id == conversation.id,
                Message.created_at >= time_window
            ).order_by(Message.created_at).limit(20).all()
            
            for msg in db_messages:
                # Skip tool calls/results stored in DB if not formatted for LangGraph yet
                # For now, we mainly care about the conversation text flow
                if msg.role == MessageRole.USER:
                    history_messages.append(HumanMessage(content=msg.content))
                elif msg.role == MessageRole.ASSISTANT:
                    history_messages.append(AIMessage(content=msg.content))
                # Note: System messages handled by _build_system_prompt
            
        except Exception as e:
            print(f"[LANGGRAPH] Warning: Failed to load history: {e}")
        
        config = {"configurable": {"thread_id": thread_id}}

        # Add current user message
        history_messages.append(HumanMessage(content=user_message))

        # ============================================================
        # EAGER LOADING: Pre-load all agent data to avoid lazy loading failures
        # This prevents "MySQL server has gone away" errors during long LLM calls
        # ============================================================
        try:
            from extensions import db
            db.session.rollback()  # Clear any stale state before loading
        except Exception:
            pass
        
        # Pre-fetch all agent features into a Python list (avoids future DB queries)
        enabled_feature_names = [f.name for f in agent.features.filter_by(is_enabled=True).all()]
        agent_name = agent.name
        agent_id = agent.id
        agent_instructions = agent.system_prompt or ''
        conversation_id = conversation.id
        contact_phone = conversation.contact_phone
        contact_email = conversation.contact_email
        contact_name = conversation.contact_name
        company_id = self.company.id if self.company else None
        
        initial_state = {
            "messages": history_messages,
            "company_id": company_id,
            "agent_id": agent_id,
            "conversation_id": conversation_id,
            "agent_name": agent_name,
            "agent_instructions": agent_instructions,
            "enabled_features": enabled_feature_names,
            "channel": channel,
            "contact_phone": contact_phone,
            "contact_email": contact_email,
            "contact_name": contact_name,
            "rag_namespace": str(company_id) if company_id else None,
            "tool_results": [],
            "last_tool_call": None
        }
        
        try:
            # Run the graph
            result = graph.invoke(initial_state, config)
            
            # Extract final response
            messages = result.get("messages", [])
            
            # Find the last AI message (not a tool message)
            final_content = ""
            tool_calls = []
            
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    final_content = msg.content
                    tool_calls = getattr(msg, 'tool_calls', [])
                    break
            
            print(f"[LANGGRAPH] Response: {final_content[:100]}...")
            
            return {
                "content": final_content,
                "tool_calls": tool_calls,
                "agent_name": agent.name
            }
            
        except Exception as e:
            print(f"[LANGGRAPH] Error: {str(e)}")
            return {
                "content": f"I encountered an error processing your message. Please try again.",
                "error": True,
                "error_details": str(e)
            }


# ============================================================
# Factory Function
# ============================================================

def get_langgraph_agent(company: Company) -> LangGraphAgentService:
    """Get LangGraph agent service for a company"""
    return LangGraphAgentService(company)
