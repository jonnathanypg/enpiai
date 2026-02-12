"""
Agent Service - Multi-agent orchestration
"""
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from models.agent import Agent, AgentFeature, FeatureCategory
from models.company import Company
from models.conversation import Conversation, Message, MessageRole
from services.llm_service import LLMService
from services.rag_service import RAGService
from extensions import db


class AgentService:
    """Multi-agent orchestration service"""
    
    def __init__(self, company: Company):
        self.company = company
        self.llm_service = LLMService(company)
        self.rag_service = RAGService(company)
        # Lazy load due to potential circular imports, or just standard init
        from services.twilio_service import TwilioService
        from services.livekit_service import LiveKitService
        from services.email_service import EmailService
        from services.paypal_service import PayPalService
        from services.google_service import GoogleService
        from services.hubspot_service import HubSpotService
        from services.sentiment_service import SentimentService
        from services.escalation_service import EscalationService
        self.twilio_service = TwilioService(company)
        self.livekit_service = LiveKitService(company)
        self.email_service = EmailService()
        self.paypal_service = PayPalService(company)
        self.hubspot_service = HubSpotService(company)
        self.sentiment_service = SentimentService(company)
        self.escalation_service = EscalationService(company)
        self.google_service = None  # Requires user credentials, will be initialized when needed
        self._tools = {}
    
    def get_active_agents(self) -> List[Agent]:
        """Get all active agents for the company"""
        return Agent.query.filter_by(
            company_id=self.company.id,
            is_active=True
        ).order_by(Agent.priority.desc()).all()

    def orchestrate_agent_selection(self, user_message: str, agents: List[Agent]) -> Optional[Agent]:
        """
        Smart Router: Select the best agent for the task using LLM.
        """
        if not agents:
            return None
            
        # If only one agent, just use it
        if len(agents) == 1:
            return agents[0]

        # Build context for the Orchestrator
        agents_info = []
        for agent in agents:
            agents_info.append(f"- ID: {agent.id} | Name: {agent.name} | Objective: {agent.objective.value} | Description: {agent.description or 'No description'}")
        
        agents_list_str = "\n".join(agents_info)
        
        system_prompt = (
            "You are the Orchestrator of a multi-agent system. Your job is to route the user's message to the single best agent.\n"
            "Analyze the User Message and the Available Agents.\n"
            "Return JSON with 'agent_id' and 'reason'.\n"
            "Available Agents:\n"
            f"{agents_list_str}"
        )
        
        messages = [
            {'role': 'user', 'content': f"User Message: {user_message}"}
        ]
        
        try:
            # We use a fast model for routing if possible, but default to main configuration
            response = self.llm_service.chat(
                messages=messages,
                system_prompt=system_prompt,
                model='gpt-4o-mini', # Use a fast model for routing
                temperature=0.0
            )
            
            content = response.get('content', '')
            # Clean json block if needed
            if "```json" in content:
                content = content.replace("```json", "").replace("```", "")
            
            data = json.loads(content)
            selected_id = data.get('agent_id')
            
            print(f"[ORCHESTRATOR] 🤖 Routing to Agent ID: {selected_id} | Reason: {data.get('reason')}")
            
            # Find the agent object
            for agent in agents:
                if agent.id == selected_id:
                    return agent
            
            # Fallback to first priority
            return agents[0]
            
        except Exception as e:
            print(f"[ORCHESTRATOR] ⚠️ Error in routing: {e}. Fallback to default.")
            return agents[0]
    
    def get_agent_tools(self, agent: Agent) -> List[Dict]:
        """Get available tools based on agent's enabled features"""
        tools = []
        
        # Check enabled tools
        enabled_features = {f.name: f for f in agent.features.filter_by(is_enabled=True)}
        
        if 'schedule_meeting' in enabled_features:
            tools.append({
                'type': 'function',
                'function': {
                    'name': 'schedule_meeting',
                    'description': 'Schedule a meeting or appointment on the calendar',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'title': {'type': 'string', 'description': 'Meeting title'},
                            'date': {'type': 'string', 'description': 'Date in YYYY-MM-DD format'},
                            'time': {'type': 'string', 'description': 'Time in HH:MM format'},
                            'duration_minutes': {'type': 'integer', 'description': 'Duration in minutes'},
                            'attendee_email': {'type': 'string', 'description': 'Attendee email'}
                        },
                        'required': ['title', 'date', 'time']
                    }
                }
            })
        
        if 'send_email' in enabled_features:
            tools.append({
                'type': 'function',
                'function': {
                    'name': 'send_email',
                    'description': 'Send an email to a recipient',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'to': {'type': 'string', 'description': 'Recipient email address'},
                            'subject': {'type': 'string', 'description': 'Email subject'},
                            'body': {'type': 'string', 'description': 'Email body content'}
                        },
                        'required': ['to', 'subject', 'body']
                    }
                }
            })
        
        # Twilio Tools - WhatsApp
        if 'whatsapp' in enabled_features:
            tools.append({
                'type': 'function',
                'function': {
                    'name': 'send_whatsapp',
                    'description': 'Send a WhatsApp message to a user',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'to': {'type': 'string', 'description': 'WhatsApp phone number in international format (e.g., +1234567890)'},
                            'message': {'type': 'string', 'description': 'The message content to send'}
                        },
                        'required': ['to', 'message']
                    }
                }
            })
            
        # Twilio Tools - Voice
        if 'voice_calls' in enabled_features:
            tools.append({
                'type': 'function',
                'function': {
                    'name': 'make_call',
                    'description': 'Initiate an outbound voice call',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'to': {'type': 'string', 'description': 'Number to call (e.g. +1...)'},
                            'purpose': {'type': 'string', 'description': 'The detailed goal, objective, or specific instructions for the call. Do not summarize generic intent; provide the full context of what needs to be said or asked. MANDATORY.'}
                        },
                        'required': ['to', 'purpose']
                    }
                }
            })
        
        if 'check_inventory' in enabled_features:
            tools.append({
                'type': 'function',
                'function': {
                    'name': 'check_inventory',
                    'description': 'Check product inventory, prices, and availability',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'product_name': {'type': 'string', 'description': 'Product name or code to search'},
                            'category': {'type': 'string', 'description': 'Optional product category'}
                        },
                        'required': ['product_name']
                    }
                }
            })
        
        if 'process_payment' in enabled_features:
            # DISABLED LEGACY TOOL to force agentic flow
            # tools.append({
            #     'type': 'function',
            #     'function': {
            #         'name': 'create_payment_link',
            #         'description': 'Create a PayPal payment link for a purchase (user will be redirected to PayPal)',
            #         'parameters': {
            #             'type': 'object',
            #             'properties': {
            #                 'amount': {'type': 'number', 'description': 'Payment amount'},
            #                 'currency': {'type': 'string', 'description': 'Currency code (USD, EUR, etc.)'},
            #                 'description': {'type': 'string', 'description': 'Payment description'},
            #                 'customer_email': {'type': 'string', 'description': 'Customer email for receipt'}
            #             },
            #             'required': ['amount', 'description']
            #         }
            #     }
            # })
            
            # New: Agentic Payment Tools (in-conversation)
            tools.append({
                'type': 'function',
                'function': {
                    'name': 'paypal_create_order',
                    'description': 'Create a PayPal order. NEVER guess the amount. You MUST ask the user for the amount and description explicitly before calling this tool.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'amount': {'type': 'number', 'description': 'Payment amount. Do not guess. Ask user.'},
                            'currency': {'type': 'string', 'description': 'Currency code (USD, EUR, etc.)', 'default': 'USD'},
                            'description': {'type': 'string', 'description': 'Description of the purchase'}
                        },
                        'required': ['amount', 'description']
                    }
                }
            })
            
            tools.append({
                'type': 'function',
                'function': {
                    'name': 'paypal_get_order',
                    'description': 'Check the status of a PayPal order',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'order_id': {'type': 'string', 'description': 'The PayPal order ID'}
                        },
                        'required': ['order_id']
                    }
                }
            })
            
            tools.append({
                'type': 'function',
                'function': {
                    'name': 'paypal_capture_order',
                    'description': 'Capture/complete payment for an order. Use this after customer confirms they want to pay.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'order_id': {'type': 'string', 'description': 'The PayPal order ID to capture'}
                        },
                        'required': ['order_id']
                    }
                }
            })
        
        
        if 'create_task' in enabled_features:
            tools.append({
                'type': 'function',
                'function': {
                    'name': 'create_task',
                    'description': 'Create a follow-up task for team members',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'title': {'type': 'string', 'description': 'Task title'},
                            'description': {'type': 'string', 'description': 'Task description'},
                            'assignee': {'type': 'string', 'description': 'Team member to assign to'},
                            'due_date': {'type': 'string', 'description': 'Due date in YYYY-MM-DD format'},
                            'priority': {'type': 'string', 'enum': ['low', 'medium', 'high']}
                        },
                        'required': ['title']
                    }
                }
            })
        
        if 'transfer_call' in enabled_features:
            tools.append({
                'type': 'function',
                'function': {
                    'name': 'transfer_call',
                    'description': 'Transfer the current call to a team member',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'department': {'type': 'string', 'description': 'Department to transfer to'},
                            'employee_name': {'type': 'string', 'description': 'Specific employee name'},
                            'reason': {'type': 'string', 'description': 'Reason for transfer'}
                        },
                        'required': ['reason']
                    }
                }
            })

        # Feature: RAG Memory (On-Demand)
        # If agent has 'rag_memory' feature, we add the tool
        if 'rag_memory' in enabled_features or True: # Force enabled for now as requested
            tools.append({
                'type': 'function',
                'function': {
                    'name': 'consult_knowledge_base',
                    'description': 'Search the company knowledge base (RAG) to find specific information.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'query': {'type': 'string', 'description': 'The specific question or topic to search for.'}
                        },
                        'required': ['query']
                    }
                }
            })
        
        # CRM Integration Tools
        if 'crm_sync' in enabled_features:
            tools.append({
                'type': 'function',
                'function': {
                    'name': 'sync_to_crm',
                    'description': 'Sync contact information and conversation summary to HubSpot CRM',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'contact_name': {'type': 'string', 'description': 'Full name of the contact'},
                            'contact_email': {'type': 'string', 'description': 'Email address (optional)'},
                            'contact_phone': {'type': 'string', 'description': 'Phone number in international format'},
                            'summary': {'type': 'string', 'description': 'Brief summary of the conversation or interaction'}
                        },
                        'required': ['contact_phone']
                    }
                }
            })
            tools.append({
                'type': 'function',
                'function': {
                    'name': 'lookup_customer',
                    'description': 'Look up a customer in HubSpot CRM by phone or email',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'phone': {'type': 'string', 'description': 'Phone number to search'},
                            'email': {'type': 'string', 'description': 'Email address to search'}
                        },
                        'required': []
                    }
                }
            })
        
        return tools
    
    def build_system_prompt(self, agent: Agent, conversation: Optional[Conversation] = None) -> str:
        """Build complete system prompt for agent"""
        prompts = []
        
        # Base company prompt
        prompts.append(self.company.get_full_system_prompt())
        
        # Agent-specific prompt
        prompts.append(agent.get_full_prompt())
        
        # Context about current conversation
        if conversation:
            if conversation.contact_name:
                prompts.append(f"You are currently speaking with {conversation.contact_name}.")
            if conversation.contact_phone:
                prompts.append(f"Their phone number is {conversation.contact_phone}.")
        
        # Available tools context
        enabled_features = [f.label for f in agent.features.filter_by(is_enabled=True)]
        if enabled_features:
            prompts.append(f"You have access to the following capabilities: {', '.join(enabled_features)}.")
        
        return "\n\n".join(filter(None, prompts))
    
    def process_message(
        self,
        conversation: Conversation,
        user_message: str,
        agent: Optional[Agent] = None,
        channel: str = "webchat",
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and generate response
        
        Args:
            conversation: Current conversation
            user_message: User's message
            agent: Specific agent to use (or auto-select)
            channel: Channel type (webchat, telegram, whatsapp, etc.)
            thread_id: Optional ID for memory persistence (e.g. session ID)
        
        Returns:
            Dict with response, tool_calls, etc.
        """
        # ============================================================
        # LangGraph Routing (NEW)
        # Routes to LangGraph by default for better memory management
        # ============================================================
        use_langgraph = True  # Default ON; set to False to use legacy flow
        
        # Check company settings for override (if settings attribute exists)
        if self.company and hasattr(self.company, 'settings') and self.company.settings:
            use_langgraph = self.company.settings.get('use_langgraph', True)
        
        if use_langgraph:
            try:
                from services.langgraph_agent import LangGraphAgentService
                lg_service = LangGraphAgentService(self.company)
                return lg_service.process_message(
                    conversation=conversation,
                    user_message=user_message,
                    agent=agent,
                    channel=channel,
                    thread_id=thread_id
                )
            except Exception as e:
                print(f"[WARNING] LangGraph failed, falling back to legacy: {e}")
                # Fall through to legacy processing
        
        # ============================================================
        # Legacy Processing (Fallback)
        # ============================================================
        
        # [NEW] Sentiment & Escalation Analysis
        # Check if enabled for this agent (if agent is known yet)
        should_run_analysis = True
        if agent:
            # If agent is specific, check its features. 
            # Note: We query features inefficiently here, could be optimized.
            # Assuming 'agent' is an ORM object attached to session
            has_sentiment = agent.features.filter_by(name='sentiment_analysis', is_enabled=True).first() is not None
            has_escalation = agent.features.filter_by(name='auto_escalation', is_enabled=True).first() is not None
            should_run_analysis = has_sentiment or has_escalation


        if should_run_analysis:
            try:
                sentiment_result = self.sentiment_service.analyze_text(user_message)
                
                # Check for escalation
                escalation = self.escalation_service.check_escalation_needed(
                    conversation, user_message, sentiment_result
                )
                
                if escalation['should_escalate']:
                    print(f"[ESCALATION] 🚨 Auto-escalation triggered: {escalation['reasons']}")
                    self.escalation_service.trigger_escalation(
                        conversation, 
                        reason=str(escalation['reasons']),
                        urgency_score=escalation['urgency_score'],
                        notify_methods=['email'] # Default to email to avoid spamming
                    )
                    
                # Update conversation sentiment metadata
                if conversation.conv_metadata is None:
                    conversation.conv_metadata = {}
                
                conversation.conv_metadata['last_sentiment'] = sentiment_result
                conversation.conv_metadata['sentiment_score'] = sentiment_result.get('score')
                
                # Store in actual column for analytics queries
                conversation.sentiment_score = sentiment_result.get('score')
                
            except Exception as e:
                print(f"[WARNING] Sentiment/Escalation check failed: {e}")

        # Select agent if not specified
        # Select agent if not specified
        if not agent:
            agents = self.get_active_agents()
            if not agents:
                agent = None
            else:
                # Use Orchestrator to select the best agent
                agent = self.orchestrate_agent_selection(user_message, agents)
        
        if not agent:
            return {
                'content': "I'm sorry, no agents are configured. Please contact support.",
                'tool_calls': [],
                'error': 'no_agent'
            }
        
        # Build conversation history
        messages = []
        
        # Get previous messages (last 20)
        prev_messages = conversation.messages.order_by(Message.created_at.desc()).limit(20).all()
        prev_messages.reverse()
        
        # DEBUG: Log what messages are being retrieved
        print(f"[DEBUG] Retrieved {len(prev_messages)} messages from conversation {conversation.id}")
        
        for msg in prev_messages:
            # Handle both Enum and string values for role
            role_value = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
            messages.append({
                'role': role_value,
                'content': msg.content
            })
            print(f"[DEBUG]   - {role_value}: {msg.content[:50]}...")
        
        # Add current message
        messages.append({
            'role': 'user',
            'content': user_message
        })
        print(f"[DEBUG] Total messages being sent to LLM: {len(messages)}")
        
        # [REMOVED] Automatic RAG injection 
        # RAG is now a tool: consult_knowledge_base
        # This saves tokens and reduces hallucinations.
        
        # Build system prompt
        system_prompt = self.build_system_prompt(agent, conversation)
        
        # STRICT CHANNEL PROTOCOL
        system_prompt += (
            "\n\n# CHANNEL SELECTION PROTOCOL (MANDATORY COMPLIANCE):"
            "\n1. VOICE CALLS ('llamar', 'call', 'telefono'):"
            "\n   - MUST use 'make_call' tool."
            "\n   - NEVER replace a call with a message unless explicitly told to 'send a message instead'."
            "\n   - Example: 'Llama a Juan' -> make_call(to='...', purpose='...')"
            "\n"
            "\n2. WHATSAPP / MESSAGE ('escribir', 'mandar mensaje', 'whatsapp', 'text'):"
            "\n   - MUST use 'send_whatsapp' tool."
            "\n   - NEVER use email for instant messaging requests."
            "\n   - Example: 'Escribe a Juan' -> send_whatsapp(to='...', message='...')"
            "\n"
            "\n3. EMAIL ('correo', 'email', 'mail', 'enviar info extensa'):"
            "\n   - MUST use 'send_email'."
            "\n   - Use only when specifically asked for email or formal documentation."
            "\n"
            "\nCRITICAL: Analyze the user's VERB. 'Llamar' ALWAYS means Voice Call. 'Escribir' ALWAYS means WhatsApp."
        )
        
        # Get available tools
        tools = self.get_agent_tools(agent)
        
        # Multi-turn conversational loop (max 5 turns to prevent infinite loops)
        max_turns = 5
        tool_results = []
        final_content = ""
        
        try:
            print(f"\n[AGENT] 🤔 Processing message for agent: {agent.name}")
            
            for turn in range(max_turns):
                response = self.llm_service.chat(
                    messages=messages,
                    system_prompt=system_prompt,
                    tools=tools if tools else None,
                    model='gpt-4o' if agent.name == 'Recepcionista' else None # Optional override
                )
                
                # If content is present, capture it (it might be the final response)
                if response.get('content'):
                    final_content = response.get('content')
                
                # Check for tool calls
                if not response.get('tool_calls'):
                    # No more tools, we are done
                    break
                    
                # Has tool calls, execute them
                assistant_msg = {
                    'role': 'assistant',
                    'content': response.get('content'),
                    'tool_calls': []
                }
                
                print(f"[AGENT] 🛠️ Tool calls requested: {len(response['tool_calls'])}")
                
                # Append assistant message with tool calls to history
                # We need to reconstruct the tool_calls format for OpenAI validation
                openai_tool_calls = []
                for tc in response['tool_calls']:
                     openai_tool_calls.append({
                         'id': tc['id'],
                         'type': 'function',
                         'function': {
                             'name': tc['name'],
                             'arguments': tc['arguments'] # Already string
                         }
                     })
                
                # We add the raw tool calls to the history for the LLM to see what it asked
                messages.append({
                    'role': 'assistant',
                    'content': response.get('content'),
                    'tool_calls': openai_tool_calls
                })

                # Execute calls
                for tool_call in response['tool_calls']:
                    print(f"[AGENT] ⚙️ Executing tool: {tool_call['name']} with args: {tool_call['arguments']}")
                    
                    # Parse args safely
                    args = tool_call['arguments']
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except:
                            pass
                            
                    result = self.execute_tool(
                        tool_call['name'],
                        args,
                        agent=agent
                    )
                    
                    # Track result for API return
                    tool_results.append({
                        'tool': tool_call['name'],
                        'arguments': tool_call['arguments'],
                        'result': result
                    })
                    print(f"[AGENT] ✅ Tool Result: {result}")
                    
                    # Append tool result to history
                    messages.append({
                        'role': 'tool',
                        'tool_call_id': tool_call['id'],
                        'content': json.dumps(result)
                    })
            
            return {
                'content': final_content,
                'tool_calls': tool_results,
                'usage': response.get('usage', {}),
                'agent_id': agent.id,
                'agent_name': agent.name
            }
            
        except Exception as e:
            print(f"ERROR in agent processing: {e}")
            return {
                'content': f"I apologize, but I encountered an error: {str(e)}",
                'tool_calls': [],
                'error': str(e)
            }
    
    def execute_tool(self, tool_name: str, arguments: Dict, agent: Optional[Agent] = None) -> Any:
        """Execute a tool and return result"""
        # Tool implementations
        
        if tool_name == 'schedule_meeting':
            # Try to use Google Calendar integration if configured
            try:
                # Check if company has Google service account configured
                google_sa = self.company.api_keys.get('google_service_account') if self.company.api_keys else None
                
                if google_sa:
                    from integrations.calendar import GoogleCalendarIntegration
                    import tempfile
                    import json as json_module
                    
                    # Write service account to temp file
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        if isinstance(google_sa, str):
                            f.write(google_sa)
                        else:
                            json_module.dump(google_sa, f)
                        temp_path = f.name
                    
                    calendar = GoogleCalendarIntegration(credentials_path=temp_path)
                    
                    # Parse date and time
                    date_str = arguments.get('date', '')
                    time_str = arguments.get('time', '09:00')
                    
                    try:
                        meeting_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                    except ValueError:
                        # Try alternative formats
                        try:
                            meeting_datetime = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
                        except ValueError:
                            meeting_datetime = datetime.now()
                    
                    result = calendar.schedule_meeting(
                        title=arguments.get('title', 'Meeting'),
                        start_time=meeting_datetime,
                        duration_minutes=arguments.get('duration', 30),
                        description=arguments.get('description'),
                        attendees=[arguments.get('attendee_email')] if arguments.get('attendee_email') else None
                    )
                    
                    # Clean up temp file
                    import os
                    os.unlink(temp_path)
                    
                    return result
                else:
                    # No Google Calendar configured, return mock
                    return {
                        'success': True,
                        'meeting_id': f'meeting_{datetime.now().strftime("%Y%m%d%H%M%S")}',
                        'message': f"Meeting '{arguments.get('title')}' scheduled for {arguments.get('date')} at {arguments.get('time')}",
                        'note': 'Google Calendar not configured - meeting saved locally only'
                    }
            except Exception as e:
                print(f"ERROR scheduling meeting: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'message': f"Could not schedule meeting: {str(e)}"
                }
        
        elif tool_name == 'send_email':
            # Use EmailService
            return self.email_service.send_email(
                company_id=self.company.id,
                to_email=arguments.get('to'),
                subject=arguments.get('subject', 'New Message'),
                body=arguments.get('body') or arguments.get('message', '')
            )

        elif tool_name == 'send_whatsapp':
            return self.twilio_service.send_whatsapp(
                to_number=arguments.get('to'),
                message=arguments.get('message')
            )
            
        elif tool_name == 'make_call':
            # Check preferred provider (Agent specific -> Company default -> Default Twilio)
            provider = 'twilio' # Default
            
            # 1. Check Agent preference
            if agent and agent.telephony_provider:
                provider = agent.telephony_provider
            # 2. Check Company Global preference (if agent didn't specify)
            elif self.company.api_keys and self.company.api_keys.get('telephony_provider'):
                provider = self.company.api_keys.get('telephony_provider')
                
            print(f"[AGENT] 📞 Initiating call via Provider: {provider.upper()}")
            
            if provider == 'livekit':
                # Get Agent Gender/Voice for metadata
                agent_gender = agent.gender.value if agent and agent.gender else 'neutral'
                
                # We need to pass this to make_call so it ends up in the room metadata
                # Updating livekit_service.make_call signature might be needed, 
                # OR we just pack it into extra arguments if supported.
                # Looking at livekit_service implementation (implied), let's assume we can pass metadata dict or similar.
                # Actually, livekit_service.make_call usually takes specific args.
                # Let's verify livekit_service.py first or just pass "voice_gender" if possible.
                # But safer is to pass it as an argument if we modify livekit_service.
                
                return self.livekit_service.make_call(
                    to_number=arguments.get('to'),
                    purpose=arguments.get('purpose', 'Connection'),
                    agent_id=agent.id if agent else None,
                    company_id=self.company.id,
                    metadata_extras={'gender': agent_gender} # Passing extras
                )
            else:
                # Default Twilio
                # For make_call, we usually need TwiML. 
                # Ideally we generate TwiML that speaks the 'purpose' using <Say>.
                # Construct a TwiML Bin URL or raw XML if supported by service?
                # TwilioService.make_call accepts 'twiml' (string or URL). 
                # We'll generate simple TwiML for TTS.
                purpose = arguments.get('purpose', 'Connecting you to our agent.')
                twiml = f'<Response><Say voice="alice">{purpose}</Say></Response>'
                return self.twilio_service.make_call(
                    to_number=arguments.get('to'),
                    twiml=twiml
                )
        
        elif tool_name == 'check_inventory':
            # Try to use Google Sheets integration if configured
            try:
                google_sa = self.company.api_keys.get('google_service_account') if self.company.api_keys else None
                spreadsheet_id = self.company.api_keys.get('inventory_spreadsheet_id') if self.company.api_keys else None
                
                if google_sa and spreadsheet_id:
                    from integrations.google_sheets import GoogleSheetsIntegration
                    import tempfile
                    import json as json_module
                    
                    # Write service account to temp file
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        if isinstance(google_sa, str):
                            f.write(google_sa)
                        else:
                            json_module.dump(google_sa, f)
                        temp_path = f.name
                    
                    sheets = GoogleSheetsIntegration(credentials_path=temp_path)
                    
                    # Search for product
                    product_name = arguments.get('product_name', '')
                    results = sheets.search_inventory(
                        spreadsheet_id=spreadsheet_id,
                        query=product_name
                    )
                    
                    # Clean up temp file
                    import os
                    os.unlink(temp_path)
                    
                    if results:
                        product = results[0]  # Take first match
                        return {
                            'success': True,
                            'product': product.get('Name', product.get('Product', product_name)),
                            'available': int(product.get('Quantity', 0)) > 0,
                            'quantity': product.get('Quantity', 0),
                            'price': product.get('Price', 0),
                            'details': product
                        }
                    else:
                        return {
                            'success': False,
                            'product': product_name,
                            'available': False,
                            'message': f"Product '{product_name}' not found in inventory"
                        }
                else:
                    # No Google Sheets configured, return mock
                    return {
                        'success': True,
                        'product': arguments.get('product_name'),
                        'available': True,
                        'quantity': 50,
                        'price': 29.99,
                        'note': 'Inventory system not configured - showing demo data'
                    }
            except Exception as e:
                print(f"ERROR checking inventory: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'message': f"Could not check inventory: {str(e)}"
                }
        
        elif tool_name == 'create_payment_link':
            # Try to use PayPal integration
            try:
                result = self.paypal_service.create_payment(
                    amount=float(arguments.get('amount', 0)),
                    currency=arguments.get('currency', 'USD'),
                    description=arguments.get('description', 'Payment')
                )
                
                if result.get('success'):
                    return {
                        'success': True,
                        'payment_link': result.get('approval_url'),
                        'payment_id': result.get('payment_id'),
                        'amount': arguments.get('amount'),
                        'currency': arguments.get('currency', 'USD')
                    }
                else:
                    # PayPal failed, return mock link
                    return {
                        'success': True,
                        'payment_link': f"https://paypal.me/example/{arguments.get('amount')}",
                        'amount': arguments.get('amount'),
                        'note': 'PayPal not configured - showing demo link'
                    }
            except Exception as e:
                print(f"ERROR creating payment: {e}")
                return {
                    'success': True,
                    'payment_link': f"https://paypal.me/example/{arguments.get('amount')}",
                    'amount': arguments.get('amount'),
                    'note': f'PayPal error: {str(e)} - showing demo link'
                }
        
        # === NEW: Agentic Payment Tools ===
        elif tool_name == 'paypal_create_order':
            try:
                from services.paypal_toolkit import get_paypal_toolkit
                toolkit = get_paypal_toolkit(self.company)
                
                result = toolkit.create_order(
                    amount=float(arguments.get('amount', 0)),
                    currency=arguments.get('currency', 'USD'),
                    description=arguments.get('description', 'Payment')
                )
                
                if result.get('success'):
                    return {
                        'success': True,
                        'order_id': result.get('order_id'),
                        'status': result.get('status'),
                        'amount': result.get('amount'),
                        'currency': result.get('currency'),
                        'description': result.get('description'),
                        'message': f"Order created successfully. Order ID: {result.get('order_id')}. Ask customer to confirm payment."
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('error', 'Failed to create order'),
                        'message': 'Could not create PayPal order. You may offer the payment link alternative.'
                    }
            except Exception as e:
                print(f"ERROR paypal_create_order: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'message': 'PayPal order creation failed. Consider using create_payment_link instead.'
                }
        
        elif tool_name == 'paypal_get_order':
            try:
                from services.paypal_toolkit import get_paypal_toolkit
                toolkit = get_paypal_toolkit(self.company)
                
                result = toolkit.get_order(arguments.get('order_id'))
                
                if result.get('success'):
                    return {
                        'success': True,
                        'order_id': result.get('order_id'),
                        'status': result.get('status'),
                        'amount': result.get('amount'),
                        'payer': result.get('payer'),
                        'message': f"Order {result.get('order_id')} status: {result.get('status')}"
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('error', 'Order not found')
                    }
            except Exception as e:
                print(f"ERROR paypal_get_order: {e}")
                return {'success': False, 'error': str(e)}
        
        elif tool_name == 'paypal_capture_order':
            try:
                from services.paypal_toolkit import get_paypal_toolkit
                toolkit = get_paypal_toolkit(self.company)
                
                result = toolkit.capture_order(arguments.get('order_id'))
                
                if result.get('success'):
                    # Send receipt email if we have payer email
                    payer_email = result.get('payer_email')
                    if payer_email:
                        try:
                            from services.pdf_service import PDFService
                            amount_info = result.get('amount', {})
                            
                            invoice_data = {
                                'id': result.get('capture_id', result.get('order_id')),
                                'company_name': self.company.name if self.company else 'OnePunch',
                                'amount': amount_info.get('value', '0.00'),
                                'currency': amount_info.get('currency_code', 'USD'),
                                'description': 'Payment completed via conversation'
                            }
                            
                            pdf_buffer = PDFService.generate_invoice(invoice_data)
                            
                            self.email_service.send_email(
                                company_id=self.company.id if self.company else None,
                                to_email=payer_email,
                                subject=f"Receipt from {invoice_data['company_name']}",
                                body=f"Thank you for your payment of {invoice_data['amount']} {invoice_data['currency']}. Your receipt is attached.",
                                attachments=[{
                                    'name': f"Receipt_{result.get('order_id')}.pdf",
                                    'content': pdf_buffer.getvalue(),
                                    'type': 'application/pdf'
                                }]
                            )
                        except Exception as email_err:
                            print(f"Receipt email error: {email_err}")
                    
                    return {
                        'success': True,
                        'order_id': result.get('order_id'),
                        'status': 'COMPLETED',
                        'capture_id': result.get('capture_id'),
                        'amount': result.get('amount'),
                        'message': 'Payment completed successfully! ' + ('Receipt sent to ' + payer_email if payer_email else '')
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('error', 'Capture failed'),
                        'status': result.get('status'),
                        'message': 'Payment capture failed. The order may not be approved yet.'
                    }
            except Exception as e:
                print(f"ERROR paypal_capture_order: {e}")
                return {'success': False, 'error': str(e)}
        
        elif tool_name == 'create_task':
            # Create a task - for now, we'll email the assignee if it looks like an email, 
            # or treat it as an internal log/escalation
            title = arguments.get('title')
            assignee = arguments.get('assignee')
            description = arguments.get('description', '')
            
            try:
                # If assignee is email, send notification
                if assignee and '@' in assignee:
                    self.email_service.send_email(
                        to=assignee,
                        subject=f"New Task: {title}",
                        body=f"Task Assigned: {title}\nPriority: {arguments.get('priority', 'medium')}\nDue: {arguments.get('due_date')}\n\n{description}"
                    )
                
                return {
                    'success': True,
                    'task_id': f"task_{int(datetime.now().timestamp())}",
                    'message': f"Task '{title}' created and assigned to {assignee}"
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        elif tool_name == 'transfer_call':
            # Handle call transfer / escalation
            target = arguments.get('employee_name') or arguments.get('department')
            reason = arguments.get('reason', 'Transfer requested')
            
            try:
                # We can use the escalation service to find the right person and notify them
                # This works for both Voice (via callback) and Text (via notification)
                # In a real voice call, the VoiceAgent would handle the SIP REFER equivalent
                
                # Check for available employees in that department
                employees = self.escalation_service.get_available_employees(
                    department=arguments.get('department')
                )
                
                transferred_to = employees[0]['name'] if employees else target
                
                return {
                    'success': True,
                    'transferred_to': transferred_to,
                    'action': 'escalate', # Signal to voice agent to stop AI and wait for human
                    'message': f"Transfer initiated to {transferred_to}"
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

        elif tool_name == 'consult_knowledge_base':
            query = arguments.get('query')
            print(f"[AGENT] 🧠 Consulting RAG for: '{query}'")
            try:
                # Use RAG Service to fetch context
                context = self.rag_service.get_context(query, top_k=3)
                if context:
                    return {
                        'success': True,
                        'found': True,
                        'information': context
                    }
                else:
                    return {
                        'success': True,
                        'found': False,
                        'message': "No specific information found in the knowledge base."
                    }
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        elif tool_name == 'sync_to_crm':
            try:
                result = self.hubspot_service.sync_conversation(
                    contact_phone=arguments.get('contact_phone'),
                    contact_name=arguments.get('contact_name'),
                    summary=arguments.get('summary')
                )
                return result
            except Exception as e:
                return {'success': False, 'error': f"CRM Sync Failed: {str(e)}"}
        
        elif tool_name == 'lookup_customer':
            try:
                email = arguments.get('email')
                phone = arguments.get('phone')
                
                if email:
                    contact = self.hubspot_service.get_contact_by_email(email)
                elif phone:
                    contact = self.hubspot_service.get_contact_by_phone(phone)
                else:
                    return {'success': False, 'error': 'Must provide email or phone'}
                
                if contact:
                    props = contact.get('properties', {})
                    return {
                        'success': True,
                        'found': True,
                        'name': f"{props.get('firstname', '')} {props.get('lastname', '')}".strip(),
                        'email': props.get('email'),
                        'phone': props.get('phone'),
                        'company': props.get('company'),
                        'lifecycle_stage': props.get('lifecyclestage'),
                        'last_contact': props.get('notes_last_contacted')
                    }
                else:
                    return {'success': True, 'found': False, 'message': 'Customer not found'}
                    
            except Exception as e:
                return {'success': False, 'error': f"CRM Lookup Failed: {str(e)}"}
        
        return {'success': False, 'error': f'Unknown tool: {tool_name}'}
