"""
Company Model - Multi-tenant company/business management
"""
from datetime import datetime
from enum import Enum
from extensions import db


class AgentGender(str, Enum):
    FEMALE = 'female'
    MALE = 'male'
    NEUTRAL = 'neutral'


class Company(db.Model):
    """Company/Business model - main tenant entity"""
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    
    # Agent Personalization
    agent_name = db.Column(db.String(100), default='Assistant')
    agent_gender = db.Column(db.Enum(AgentGender), default=AgentGender.NEUTRAL)
    personality_prompt = db.Column(db.Text, nullable=True)
    custom_instructions = db.Column(db.Text, nullable=True)
    
    # LLM Configuration
    llm_provider = db.Column(db.String(50), default='openai')
    llm_model = db.Column(db.String(100), default='gpt-4')
    voice_provider = db.Column(db.String(50), default='elevenlabs')
    voice_model = db.Column(db.String(100), nullable=True)
    
    # API Keys (encrypted in production)
    api_keys = db.Column(db.JSON, default=dict)
    
    # Pinecone RAG Configuration
    pinecone_index = db.Column(db.String(255), nullable=True)
    pinecone_namespace = db.Column(db.String(255), nullable=True)
    
    # Business Info
    industry = db.Column(db.String(100), nullable=True)
    timezone = db.Column(db.String(50), default='UTC')
    language = db.Column(db.String(10), default='en')
    
    # Location
    country = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    
    # Contact Info
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    
    # Relationships
    users = db.relationship('User', back_populates='company', lazy='dynamic')
    agents = db.relationship('Agent', back_populates='company', lazy='dynamic', cascade='all, delete-orphan')
    channels = db.relationship('Channel', back_populates='company', lazy='dynamic', cascade='all, delete-orphan')
    employees = db.relationship('Employee', back_populates='company', lazy='dynamic', cascade='all, delete-orphan')
    documents = db.relationship('Document', back_populates='company', lazy='dynamic', cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', back_populates='company', lazy='dynamic', cascade='all, delete-orphan')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    subscription_tier = db.Column(db.String(50), default='free')
    
    def get_full_system_prompt(self):
        """Generate complete system prompt including personality"""
        base_prompt = f"You are {self.agent_name}, an AI assistant"
        
        if self.agent_gender != AgentGender.NEUTRAL:
            base_prompt += f" ({self.agent_gender.value})"
        
        base_prompt += f" for {self.name}."
        
        if self.personality_prompt:
            base_prompt += f"\n\nPersonality: {self.personality_prompt}"
        
        if self.custom_instructions:
            base_prompt += f"\n\nSpecial Instructions: {self.custom_instructions}"
        
        return base_prompt
    
    def to_dict(self, include_api_keys=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'agent_name': self.agent_name,
            'agent_gender': self.agent_gender.value,
            'personality_prompt': self.personality_prompt,
            'custom_instructions': self.custom_instructions,
            'llm_provider': self.llm_provider,
            'llm_model': self.llm_model,
            'voice_provider': self.voice_provider,
            'voice_model': self.voice_model,
            'pinecone_index': self.pinecone_index,
            'industry': self.industry,
            'country': self.country,
            'city': self.city,
            'timezone': self.timezone,
            'language': self.language,
            'email': self.email,
            'phone': self.phone,
            'website': self.website,
            'is_active': self.is_active,
            'subscription_tier': self.subscription_tier,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_api_keys:
            data['api_keys'] = self.api_keys
        
        return data
    
    def __repr__(self):
        return f'<Company {self.name}>'
