"""
Agent Configuration Model - Per-distributor AI agent setup with features.
Migration Path: Agent configs will be stored in user-controlled encrypted vaults.
"""
from datetime import datetime
from enum import Enum
from extensions import db


class AgentTone(str, Enum):
    PROFESSIONAL = 'professional'
    FRIENDLY = 'friendly'
    FORMAL = 'formal'
    CASUAL = 'casual'
    SALES = 'sales'
    SUPPORT = 'support'
    WELLNESS_COACH = 'wellness_coach'


class AgentObjective(str, Enum):
    CUSTOMER_SERVICE = 'customer_service'
    SALES = 'sales'
    SCHEDULING = 'scheduling'
    LEAD_QUALIFICATION = 'lead_qualification'
    WELLNESS_EVALUATION = 'wellness_evaluation'
    DISTRIBUTOR_ASSISTANT = 'distributor_assistant'
    GENERAL = 'general'


class FeatureCategory(str, Enum):
    CHANNEL = 'channel'
    INTEGRATION = 'integration'
    SKILL = 'skill'
    AI_FEATURE = 'ai_feature'


class AgentConfig(db.Model):
    """Agent configuration model — one or more per distributor"""
    __tablename__ = 'agent_configs'

    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False)

    # Basic Info
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    agent_type = db.Column(db.String(50), default='prospect')  # 'prospect' or 'distributor'

    # Tone & Personality
    tone = db.Column(db.Enum(AgentTone), default=AgentTone.FRIENDLY)
    objective = db.Column(db.Enum(AgentObjective), default=AgentObjective.GENERAL)

    # System Prompt (combined with distributor prompt)
    system_prompt = db.Column(db.Text, nullable=True)

    # Priority (for multi-agent orchestration)
    priority = db.Column(db.Integer, default=1)

    # Status
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    distributor = db.relationship('Distributor', back_populates='agent_configs')
    features = db.relationship('AgentFeature', back_populates='agent', lazy='dynamic', cascade='all, delete-orphan')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_enabled_features(self, category=None):
        """Get all enabled features, optionally filtered by category"""
        query = self.features.filter_by(is_enabled=True)
        if category:
            query = query.filter_by(category=category)
        return query.all()

    def has_feature(self, feature_name):
        """Check if a specific feature is enabled"""
        feature = self.features.filter_by(name=feature_name, is_enabled=True).first()
        return feature is not None

    def get_full_prompt(self):
        """Generate complete prompt including distributor and agent settings"""
        prompts = []

        # Distributor base prompt
        if self.distributor:
            prompts.append(self.distributor.get_full_system_prompt())

        # Tone prompt
        tone_prompts = {
            AgentTone.WELLNESS_COACH: "Act as a passionate and motivating wellness coach, guiding people towards a healthier life.",
            AgentTone.SALES: "Act as a persuasive yet empathetic sales advisor, understanding customer needs and presenting solutions.",
            AgentTone.SUPPORT: "Act as a patient and helpful support agent, resolving issues with clarity.",
            AgentTone.PROFESSIONAL: "Maintain a professional and respectful tone in all interactions.",
            AgentTone.FRIENDLY: "Be warm, approachable, and conversational while remaining helpful.",
            AgentTone.FORMAL: "Use formal language maintaining a respectful and professional demeanor.",
            AgentTone.CASUAL: "Be relaxed and casual without ceasing to be informative and helpful.",
        }
        prompts.append(tone_prompts.get(self.tone, ""))

        # Objective prompt
        objective_prompts = {
            AgentObjective.WELLNESS_EVALUATION: "Your main objective is to guide the user through a wellness evaluation, collecting info on health, goals, and lifestyle.",
            AgentObjective.SCHEDULING: "Your main objective is to help schedule appointments and meetings, checking calendar availability.",
            AgentObjective.SALES: "Your main objective is to understand customer needs, present Herbalife products, and close sales conversationally.",
            AgentObjective.LEAD_QUALIFICATION: "Your main objective is to qualify leads by naturally asking if they are interested in products or the business opportunity.",
            AgentObjective.CUSTOMER_SERVICE: "Your main objective is to provide excellent customer service, addressing inquiries and concerns.",
            AgentObjective.DISTRIBUTOR_ASSISTANT: "Your main objective is to assist the distributor with lead summaries, business reports, and instructions.",
        }
        prompts.append(objective_prompts.get(self.objective, ""))

        # Agent-specific prompt
        if self.system_prompt:
            prompts.append(self.system_prompt)

        return "\n\n".join(filter(None, prompts))

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'distributor_id': self.distributor_id,
            'name': self.name,
            'description': self.description,
            'agent_type': self.agent_type,
            'tone': self.tone.value if self.tone else 'friendly',
            'objective': self.objective.value if self.objective else 'general',
            'system_prompt': self.system_prompt,
            'priority': self.priority,
            'is_active': self.is_active,
            'features': [f.to_dict() for f in self.features],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<AgentConfig {self.name}>'


class AgentFeature(db.Model):
    """Agent feature toggles — skills/capabilities that can be enabled/disabled"""
    __tablename__ = 'agent_features'

    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent_configs.id'), nullable=False)

    # Feature Definition
    category = db.Column(db.Enum(FeatureCategory), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    label = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # State
    is_enabled = db.Column(db.Boolean, default=False)

    # Configuration (for features that need extra settings)
    config = db.Column(db.JSON, default=dict)

    # Display order within category
    order = db.Column(db.Integer, default=0)

    # Relationships
    agent = db.relationship('AgentConfig', back_populates='features')

    # Unique constraint per agent
    __table_args__ = (
        db.UniqueConstraint('agent_id', 'name', name='unique_agent_feature'),
    )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'category': self.category.value,
            'name': self.name,
            'label': self.label,
            'description': self.description,
            'is_enabled': self.is_enabled,
            'config': self.config,
            'order': self.order
        }

    def __repr__(self):
        return f'<AgentFeature {self.name}>'


# Default features to initialize for new agents
DEFAULT_FEATURES = [
    # Channels
    {'category': FeatureCategory.CHANNEL, 'name': 'whatsapp', 'label': 'WhatsApp', 'description': 'Send and receive messages via WhatsApp', 'order': 1},
    {'category': FeatureCategory.CHANNEL, 'name': 'telegram', 'label': 'Telegram', 'description': 'Send and receive messages via Telegram', 'order': 2},
    {'category': FeatureCategory.CHANNEL, 'name': 'email', 'label': 'Email', 'description': 'Send emails', 'order': 3},
    {'category': FeatureCategory.CHANNEL, 'name': 'webchat', 'label': 'Web Chat', 'description': 'Chat widget on distributor website', 'order': 4},

    # Integrations
    {'category': FeatureCategory.INTEGRATION, 'name': 'google_calendar', 'label': 'Google Calendar', 'description': 'Schedule appointments and check availability', 'order': 1},
    {'category': FeatureCategory.INTEGRATION, 'name': 'google_gmail', 'label': 'Gmail', 'description': 'Send emails via Gmail API', 'order': 2},

    # Skills (from AGENTS.md)
    {'category': FeatureCategory.SKILL, 'name': 'knowledge_base_search', 'label': 'Knowledge Base Search', 'description': 'Search RAG knowledge base for products/ingredients', 'order': 1},
    {'category': FeatureCategory.SKILL, 'name': 'wellness_evaluation', 'label': 'Wellness Evaluation', 'description': 'Guide user through wellness evaluation', 'order': 2},
    {'category': FeatureCategory.SKILL, 'name': 'lead_qualification', 'label': 'Lead Qualification', 'description': 'Qualify prospects (customer vs business)', 'order': 3},
    {'category': FeatureCategory.SKILL, 'name': 'calendar_scheduling', 'label': 'Schedule Appointments', 'description': 'Find slots and book in Google Calendar', 'order': 4},
    {'category': FeatureCategory.SKILL, 'name': 'crm_lookup', 'label': 'CRM Lookup', 'description': 'Look up existing customer info', 'order': 5},
    {'category': FeatureCategory.SKILL, 'name': 'crm_reporting', 'label': 'CRM Reporting', 'description': 'Generate CRM reports and summaries', 'order': 6},
    {'category': FeatureCategory.SKILL, 'name': 'prospect_messaging', 'label': 'Prospect Messaging', 'description': 'Send personalized messages to leads', 'order': 7},
    {'category': FeatureCategory.SKILL, 'name': 'content_generation', 'label': 'Content Generation', 'description': 'Help create social media content', 'order': 8},

    # AI Features
    {'category': FeatureCategory.AI_FEATURE, 'name': 'rag_memory', 'label': 'RAG Memory', 'description': 'Use uploaded documents as context', 'order': 1},
    {'category': FeatureCategory.AI_FEATURE, 'name': 'conversation_history', 'label': 'Conversation History', 'description': 'Remember past conversations', 'order': 2},
    {'category': FeatureCategory.AI_FEATURE, 'name': 'sentiment_analysis', 'label': 'Sentiment Analysis', 'description': 'Analyze customer sentiment', 'order': 3},
]
