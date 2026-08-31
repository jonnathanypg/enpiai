"""
Distributor Model - Multi-tenant root entity (equivalent to Company in OnePunch).
Each Herbalife distributor is a tenant with their own data, agents, and settings.

Migration Path: Distributor identity will link to cryptographic signatures/DIDs.
Sovereign encrypted blobs will protect PII. Keys are client-side (Zero-Knowledge).
"""
import os
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
    preferred_voice = db.Column(db.String(100), nullable=True)

    # Localization
    # (Declared below in business info section)

    # LLM Configuration (Platform-managed — distributors do NOT provide their own keys)
    llm_provider = db.Column(db.String(50), default='openai')
    llm_model = db.Column(db.String(100), default=os.getenv('DEFAULT_LLM_MODEL', 'gpt-5-nano'))

    # Platform API Keys (encrypted — Sovereign SQL Layer)
    api_keys = db.Column(EncryptedJSON, nullable=True)

    # API Key for OpenAI-compatible endpoint authentication
    api_key = db.Column(db.String(255), nullable=True, unique=True, index=True)

    # Google OAuth credentials (per-distributor, via Gmail login)
    google_credentials = db.Column(EncryptedJSON, nullable=True)
    # Selected Google Calendar ID (defaults to 'primary' if not set)
    google_calendar_id = db.Column(db.String(255), nullable=True)

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

    # Nutrition Club (Club de Nutrición) Configuration
    club_name = db.Column(db.String(255), nullable=True)
    club_slogan = db.Column(db.String(255), nullable=True)
    club_address = db.Column(db.String(500), nullable=True)
    club_city = db.Column(db.String(100), nullable=True)
    club_schedule = db.Column(db.String(255), nullable=True)
    club_phone = db.Column(db.String(50), nullable=True)
    club_latitude = db.Column(db.Float, nullable=True)
    club_longitude = db.Column(db.Float, nullable=True)
    club_banner_url = db.Column(db.String(500), nullable=True)
    club_logo_url = db.Column(db.String(500), nullable=True)
    club_is_active = db.Column(db.Boolean, default=True)
    club_amenities = db.Column(db.JSON, default=list)  # e.g., ["Wi-Fi", "Degustación Gratis", "Barra Proteica"]
    club_announcement = db.Column(db.Text, nullable=True)

    # Coach Mode Configuration
    coach_mode_enabled = db.Column(db.Boolean, default=False)
    coach_music_preference = db.Column(db.String(50), default='spanish')
    coach_level_progress = db.Column(db.Integer, default=0)
    coach_daily_tasks_status = db.Column(db.JSON, nullable=True)
    coach_last_research_advice = db.Column(db.Text, nullable=True)

    # Relationships
    users = db.relationship('User', back_populates='distributor', lazy='dynamic', cascade='all, delete-orphan')
    agent_configs = db.relationship('AgentConfig', back_populates='distributor', lazy='dynamic', cascade='all, delete-orphan')
    leads = db.relationship('Lead', back_populates='distributor', lazy='dynamic', cascade='all, delete-orphan')
    customers = db.relationship('Customer', back_populates='distributor', lazy='dynamic', cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', back_populates='distributor', lazy='dynamic', cascade='all, delete-orphan')
    wellness_evaluations = db.relationship('WellnessEvaluation', back_populates='distributor', lazy='dynamic', cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', back_populates='distributor', lazy='dynamic', cascade='all, delete-orphan')
    documents = db.relationship('Document', back_populates='distributor', lazy='dynamic', cascade='all, delete-orphan')
    channels = db.relationship('Channel', back_populates='distributor', lazy='dynamic', cascade='all, delete-orphan')
    products = db.relationship('Product', back_populates='distributor', lazy='dynamic', cascade='all, delete-orphan')
    club_orders = db.relationship('ClubOrder', back_populates='distributor', lazy='dynamic', cascade='all, delete-orphan')
    subscriptions = db.relationship('Subscription', backref=db.backref('distributor_parent', uselist=False), cascade='all, delete-orphan')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Status
    is_active = db.Column(db.Boolean, default=True)
    subscription_tier = db.Column(db.Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    
    # Billing / PayPal (was dLocal)
    subscription_active = db.Column(db.Boolean, default=False)
    is_courtesy = db.Column(db.Boolean, default=False)
    subscription_plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=True)
    credits_balance = db.Column(db.Integer, default=0)
    
    # Beta / Trial Gating
    trial_activated = db.Column(db.Boolean, default=False, nullable=False)
    feedback_submitted = db.Column(db.Boolean, default=False, nullable=False)
    beta_feedback = db.Column(db.JSON, nullable=True)
    
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

    def get_google_maps_url(self) -> str:
        """Generate direct Google Maps navigation URL"""
        import urllib.parse
        if self.club_latitude and self.club_longitude:
            return f"https://www.google.com/maps/search/?api=1&query={self.club_latitude},{self.club_longitude}"
        elif self.club_address:
            addr = f"{self.club_address}, {self.club_city or ''}".strip(', ')
            return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(addr)}"
        return ""

    def get_apple_maps_url(self) -> str:
        """Generate direct Apple Maps navigation URL"""
        import urllib.parse
        club_title = self.club_name or self.business_name or "Club de Nutrición"
        if self.club_latitude and self.club_longitude:
            return f"https://maps.apple.com/?q={urllib.parse.quote(club_title)}&ll={self.club_latitude},{self.club_longitude}"
        elif self.club_address:
            addr = f"{self.club_address}, {self.club_city or ''}".strip(', ')
            return f"https://maps.apple.com/?q={urllib.parse.quote(addr)}"
        return ""

    def get_club_dict(self):
        """Get specialized public club microsite data"""
        return {
            'distributor_id': self.id,
            'distributor_name': self.name,
            'herbalife_id': self.herbalife_id,
            'club_name': self.club_name or self.business_name or f"Club de Nutrición {self.name}",
            'club_slogan': self.club_slogan or "Tu espacio de energía, nutrición y comunidad saludable",
            'club_address': self.club_address or "",
            'club_city': self.club_city or self.city or "",
            'club_schedule': self.club_schedule or "Lunes a Viernes: 07:00 - 12:00 | Sábados: 08:00 - 13:00",
            'club_phone': self.club_phone or self.whatsapp_phone or self.phone or "",
            'club_latitude': self.club_latitude,
            'club_longitude': self.club_longitude,
            'club_banner_url': self.club_banner_url or "",
            'club_logo_url': self.club_logo_url or "",
            'club_is_active': self.club_is_active if self.club_is_active is not None else True,
            'club_amenities': self.club_amenities or ["Wi-Fi", "Barra Proteica", "Degustación", "Ambiente Climatizado"],
            'club_announcement': self.club_announcement or "",
            'google_maps_url': self.get_google_maps_url(),
            'apple_maps_url': self.get_apple_maps_url(),
            'instagram': self.instagram or "",
            'facebook': self.facebook or "",
        }

    def to_dict(self, include_api_keys=False):
        """Convert to dictionary"""
        from datetime import datetime, timedelta
        in_trial = False
        if self.trial_activated and self.created_at:
            in_trial = datetime.utcnow() < (self.created_at + timedelta(hours=24))

        data = {
            'id': self.id,
            'name': self.name,
            'herbalife_id': self.herbalife_id,
            'herbalife_level': self.herbalife_level,
            'agent_name': self.agent_name,
            'agent_gender': self.agent_gender.value if self.agent_gender else 'neutral',
            'personality_prompt': self.personality_prompt,
            'custom_instructions': self.custom_instructions,
            'preferred_voice': self.preferred_voice,
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
            'club_name': self.club_name,
            'club_slogan': self.club_slogan,
            'club_address': self.club_address,
            'club_city': self.club_city,
            'club_schedule': self.club_schedule,
            'club_phone': self.club_phone,
            'club_latitude': self.club_latitude,
            'club_longitude': self.club_longitude,
            'club_banner_url': self.club_banner_url,
            'club_logo_url': self.club_logo_url,
            'club_is_active': self.club_is_active if self.club_is_active is not None else True,
            'club_amenities': self.club_amenities or [],
            'club_announcement': self.club_announcement,
            'google_maps_url': self.get_google_maps_url(),
            'apple_maps_url': self.get_apple_maps_url(),
            'is_active': self.is_active,
            'subscription_tier': self.subscription_tier.value if self.subscription_tier else 'free',
            'subscription_active': self.subscription_active or self.is_courtesy or in_trial,
            'is_in_trial': in_trial,
            'is_courtesy': self.is_courtesy,
            'trial_activated': self.trial_activated,
            'feedback_submitted': self.feedback_submitted,
            'whatsapp_connected': self.whatsapp_connected,
            'whatsapp_phone': self.whatsapp_phone,
            'google_connected': self.google_credentials is not None and bool(self.google_credentials),
            'google_calendar_id': self.google_calendar_id,
            'coach_mode_enabled': self.coach_mode_enabled,
            'coach_music_preference': self.coach_music_preference,
            'coach_level_progress': self.coach_level_progress,
            'coach_daily_tasks_status': self.coach_daily_tasks_status,
            'coach_last_research_advice': self.coach_last_research_advice,
            'created_at': (self.created_at.isoformat() + 'Z') if self.created_at else None,
            'updated_at': (self.updated_at.isoformat() + 'Z') if self.updated_at else None
        }

        if include_api_keys:
            data['api_keys'] = self.api_keys

        return data

    def __repr__(self):
        return f'<Distributor {self.name}>'
