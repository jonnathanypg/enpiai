"""
Lead Model - Prospect management for Herbalife distributors.
Migration Path: Lead data will be encrypted with client-side keys (Zero-Knowledge).
"""
from datetime import datetime
from enum import Enum
from extensions import db
from services.encryption_service import EncryptedString


class LeadStatus(str, Enum):
    NEW = 'new'
    CONTACTED = 'contacted'
    QUALIFIED = 'qualified'
    NURTURING = 'nurturing'
    CONVERTED = 'converted'
    LOST = 'lost'


class LeadSource(str, Enum):
    WHATSAPP = 'whatsapp'
    TELEGRAM = 'telegram'
    WEB_FORM = 'web_form'
    MANUAL = 'manual'
    REFERRAL = 'referral'
    SOCIAL_MEDIA = 'social_media'


class LeadType(str, Enum):
    PRODUCT_INTEREST = 'product_interest'
    BUSINESS_OPPORTUNITY = 'business_opportunity'
    UNKNOWN = 'unknown'


class Lead(db.Model):
    """Lead/Prospect model — scoped to a distributor"""
    __tablename__ = 'leads'

    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False, index=True)

    # Contact Info (PII — encrypted at rest)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    email = db.Column(EncryptedString(500), nullable=True)
    phone = db.Column(EncryptedString(500), nullable=True)

    # Location
    country = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)

    # Lead Management
    status = db.Column(db.Enum(LeadStatus), default=LeadStatus.NEW, nullable=False)
    source = db.Column(db.Enum(LeadSource), default=LeadSource.MANUAL, nullable=False)
    lead_type = db.Column(db.Enum(LeadType), default=LeadType.UNKNOWN, nullable=False)

    # Notes & context
    notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.JSON, default=list)  # e.g. ['weight_loss', 'energy', 'nutrition']

    # Flexible metadata
    lead_metadata = db.Column(db.JSON, nullable=True)

    # Relationships
    distributor = db.relationship('Distributor', back_populates='leads')
    wellness_evaluations = db.relationship('WellnessEvaluation', back_populates='lead', lazy='dynamic')
    appointments = db.relationship('Appointment', back_populates='lead', lazy='dynamic')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_contact_at = db.Column(db.DateTime, nullable=True)

    @property
    def full_name(self):
        """Returns full name"""
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or "Prospecto"

    def to_dict(self):
        return {
            'id': self.id,
            'distributor_id': self.distributor_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'country': self.country,
            'city': self.city,
            'status': self.status.value,
            'source': self.source.value,
            'lead_type': self.lead_type.value,
            'notes': self.notes,
            'tags': self.tags,
            'metadata': self.lead_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_contact_at': self.last_contact_at.isoformat() if self.last_contact_at else None
        }

    def __repr__(self):
        return f'<Lead {self.full_name}>'
