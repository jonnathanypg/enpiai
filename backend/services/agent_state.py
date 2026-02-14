"""
LangGraph State Definitions
Defines the shared state object passed between nodes in the agent graph.
Matches OnePunch architecture.
"""
import operator
from typing import TypedDict, Annotated, List, Optional, Any, Sequence
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    State shared across all nodes in the LangGraph workflow.
    
    This state is persisted between messages using a checkpointer,
    enabling conversation memory and multi-turn interactions.
    """
    
    # ============ Core Conversation ============
    # Messages accumulate using operator.add
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # ============ Multi-Tenant Context ============
    company_id: int
    agent_id: int
    conversation_id: int
    
    # ============ Agent Configuration ============
    agent_name: str
    agent_instructions: str  # System prompt from agent config
    enabled_features: List[str]  # List of enabled feature names
    
    # ============ Phase 9: Enrichment ============
    agent_hints: Optional[str]  # Sentiment/identity context hints for prompt builder
    
    # ============ Channel Context ============
    channel: str  # telegram, whatsapp, webchat, voice, email
    contact_phone: Optional[str]
    contact_email: Optional[str]
    contact_name: Optional[str]
    
    # ============ RAG Context ============
    rag_namespace: Optional[str]  # Pinecone namespace for company
    
    # ============ Tool Execution Context ============
    tool_results: List[Any]  # Results from tool executions
    last_tool_call: Optional[str]  # Name of last executed tool


class ToolContext(TypedDict):
    """
    Context passed to tools for accessing company-specific resources.
    """
    company_id: int
    company_api_keys: dict
    conversation_id: int
    channel: str
    contact_phone: Optional[str]
    contact_email: Optional[str]
