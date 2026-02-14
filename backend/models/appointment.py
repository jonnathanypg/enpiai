"""
Appointment Model - Calendar events linked to leads/customers.
Migration Path: Appointment data will be encrypted for privacy. Calendar sync remains via Google API.
"""
from datetime import datetime
from enum import Enum
from extensions import db


class AppointmentStatus(str, Enum):
    SCHEDULED = 'scheduled'
    CONFIRMED = 'confirmed'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    NO_SHOW = 'no_show'
    RESCHEDULED = 'rescheduled'


class AppointmentType(str, Enum):
    WELLNESS_CONSULTATION = 'wellness_consultation'
    PRODUCT_DEMO = 'product_demo'
    BUSINESS_OPPORTUNITY = 'business_opportunity'
    FOLLOW_UP = 'follow_up'
    OTHER = 'other'


class Appointment(db.Model):
    """Appointment model — calendar events for distributor meetings"""
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False, index=True)

    # Link to lead or customer
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)

    # Appointment details
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    appointment_type = db.Column(db.Enum(AppointmentType), default=AppointmentType.WELLNESS_CONSULTATION)

    # Scheduling
    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)
    timezone = db.Column(db.String(50), default='America/Guayaquil')

    # Location (physical or virtual)
    location = db.Column(db.String(500), nullable=True)
    meeting_link = db.Column(db.String(500), nullable=True)

    # Status
    status = db.Column(db.Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)

    # Google Calendar integration
    google_event_id = db.Column(db.String(255), nullable=True)

    # Notes
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    distributor = db.relationship('Distributor', backref='appointments')
    lead = db.relationship('Lead', back_populates='appointments')
    customer = db.relationship('Customer', back_populates='appointments')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'distributor_id': self.distributor_id,
            'lead_id': self.lead_id,
            'customer_id': self.customer_id,
            'title': self.title,
            'description': self.description,
            'appointment_type': self.appointment_type.value if self.appointment_type else None,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'duration_minutes': self.duration_minutes,
            'timezone': self.timezone,
            'location': self.location,
            'meeting_link': self.meeting_link,
            'status': self.status.value,
            'google_event_id': self.google_event_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Appointment {self.title} ({self.status.value})>'
