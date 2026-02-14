"""
Customer Model - Converted leads and existing customers.
Migration Path: Customer PII will be encrypted as sovereign blobs with client-side keys.
"""
from datetime import datetime
from extensions import db
from services.encryption_service import EncryptedString


class Customer(db.Model):
    """Customer model — converted leads or directly registered customers"""
    __tablename__ = 'customers'

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

    # Identification (PII — encrypted)
    ident_number = db.Column(EncryptedString(500), nullable=True)

    # Customer type
    customer_type = db.Column(db.String(50), default='retail')  # retail, preferred, distributor

    # If converted from a lead
    original_lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)

    # Flexible metadata (purchase history, preferences, etc.)
    customer_metadata = db.Column(db.JSON, nullable=True)

    # Relationships
    distributor = db.relationship('Distributor', back_populates='customers')
    original_lead = db.relationship('Lead', backref='converted_customer', uselist=False)
    wellness_evaluations = db.relationship('WellnessEvaluation', back_populates='customer', lazy='dynamic')
    appointments = db.relationship('Appointment', back_populates='customer', lazy='dynamic')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or "Cliente"

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
            'ident_number': self.ident_number,
            'customer_type': self.customer_type,
            'original_lead_id': self.original_lead_id,
            'metadata': self.customer_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Customer {self.full_name}>'
