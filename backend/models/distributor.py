"""
Distributor Model - Multi-tenant root entity (equivalent to Company in OnePunch).
Each Herbalife distributor is a tenant with their own data, agents, and settings.

Migration Path: Distributor identity will link to cryptographic signatures/DIDs.
Sovereign encrypted blobs will protect PII. Keys are client-side (Zero-Knowledge).
"""
from datetime import datetime
from enum import Enum
from extensions import db
from services.encryption_service import EncryptedString, EncryptedJSON


class AgentGender(str, Enum):
    FEMALE = 'female'
    MALE = 'male'
    NEUTRAL = 'neutral'


class SubscriptionTier(str, Enum):
    FREE = 'free'
    STARTER = 'starter'
    PROFESSIONAL = 'professional'
    ENTERPRISE = 'enterprise'


class Distributor(db.Model):
    """Distributor model — the main tenant entity"""
    __tablename__ = 'distributors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    # Herbalife-specific
    herbalife_id = db.Column(db.String(50), nullable=True, unique=True)
    herbalife_level = db.Column(db.String(100), nullable=True)  # e.g., "Supervisor", "World Team"

    # Agent Personalization
    agent_name = db.Column(db.String(100), default='Asistente')
    agent_gender = db.Column(db.Enum(AgentGender), default=AgentGender.NEUTRAL)
    personality_prompt = db.Column(db.Text, nullable=True)
    custom_instructions = db.Column(db.Text, nullable=True)

    # Localization
    language = db.Column(db.String(5), default='en')  # en, es, fr, pt

    # LLM Configuration (Platform-managed — distributors do NOT provide their own keys)
    llm_provider = db.Column(db.String(50), default='openai')
    llm_model = db.Column(db.String(100), default='gpt-4')

    # Platform API Keys (encrypted — Sovereign SQL Layer)
    api_keys = db.Column(EncryptedJSON, nullable=True)

    # API Key for OpenAI-compatible endpoint authentication
    api_key = db.Column(db.String(255), nullable=True, unique=True, index=True)

    # Google OAuth credentials (per-distributor, via Gmail login)
    google_credentials = db.Column(EncryptedJSON, nullable=True)

    # Pinecone RAG Configuration
    pinecone_index = db.Column(db.String(255), nullable=True)
    pinecone_namespace = db.Column(db.String(255), nullable=True)

    # Business Info
    business_name = db.Column(db.String(255), nullable=True)
    timezone = db.Column(db.String(50), default='America/Guayaquil')
    language = db.Column(db.String(10), default='es')

    # Location
    country = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)

    # Contact Info
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    instagram = db.Column(db.String(255), nullable=True)
    facebook = db.Column(db.String(255), nullable=True)

    # WhatsApp connection state
    whatsapp_connected = db.Column(db.Boolean, default=False)
    whatsapp_phone = db.Column(db.String(50), nullable=True)

    # Personal story (used by agent in conversations)
    personal_story = db.Column(db.Text, nullable=True)

    # Relationships
    users = db.relationship('User', back_populates='distributor', lazy='dynamic')
    agent_configs = db.relationship('AgentConfig', back_populates='distributor', lazy='dynamic', cascade='all, delete-orphan')
    leads = db.relationship('Lead', back_populates='distributor', lazy='dynamic', cascade='all, delete-orphan')
    customers = db.relationship('Customer', back_populates='distributor', lazy='dynamic', cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', back_populates='distributor', lazy='dynamic', cascade='all, delete-orphan')
    documents = db.relationship('Document', back_populates='distributor', lazy='dynamic', cascade='all, delete-orphan')
    channels = db.relationship('Channel', back_populates='distributor', lazy='dynamic', cascade='all, delete-orphan')
    products = db.relationship('Product', back_populates='distributor', lazy='dynamic', cascade='all, delete-orphan')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Status
    is_active = db.Column(db.Boolean, default=True)
    subscription_tier = db.Column(db.Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    
    # Billing / dLocal Go
    subscription_active = db.Column(db.Boolean, default=False)
    is_courtesy = db.Column(db.Boolean, default=False)
    subscription_plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=True)
    
    # Billing relationships
    subscription_plan = db.relationship('Plan')
    # Note: `subscriptions` is already defined in the `Subscription` model as a backref/back_populates.

    def get_full_system_prompt(self):
        """Generate complete system prompt including persona & business context"""
        base_prompt = f"Eres {self.agent_name}, un asistente virtual de IA"

        if self.agent_gender != AgentGender.NEUTRAL:
            base_prompt += f" ({self.agent_gender.value})"

        base_prompt += f" para {self.name}."

        if self.business_name:
            base_prompt += f"\nNegocio: {self.business_name}."

        if self.personal_story:
            base_prompt += f"\n\nHistoria personal del distribuidor: {self.personal_story}"

        if self.personality_prompt:
            base_prompt += f"\n\nPersonalidad: {self.personality_prompt}"

        if self.custom_instructions:
            base_prompt += f"\n\nInstrucciones especiales: {self.custom_instructions}"

        return base_prompt

    def to_dict(self, include_api_keys=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'herbalife_id': self.herbalife_id,
            'herbalife_level': self.herbalife_level,
            'agent_name': self.agent_name,
            'agent_gender': self.agent_gender.value if self.agent_gender else 'neutral',
            'personality_prompt': self.personality_prompt,
            'custom_instructions': self.custom_instructions,
            'llm_provider': self.llm_provider,
            'llm_model': self.llm_model,
            'pinecone_index': self.pinecone_index,
            'business_name': self.business_name,
            'country': self.country,
            'city': self.city,
            'timezone': self.timezone,
            'language': self.language,
            'email': self.email,
            'phone': self.phone,
            'website': self.website,
            'instagram': self.instagram,
            'facebook': self.facebook,
            'personal_story': self.personal_story,
            'is_active': self.is_active,
            'subscription_tier': self.subscription_tier.value if self.subscription_tier else 'free',
            'subscription_active': self.subscription_active,
            'is_courtesy': self.is_courtesy,
            'whatsapp_connected': self.whatsapp_connected,
            'whatsapp_phone': self.whatsapp_phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_api_keys:
            data['api_keys'] = self.api_keys

        return data

    def __repr__(self):
        return f'<Distributor {self.name}>'
