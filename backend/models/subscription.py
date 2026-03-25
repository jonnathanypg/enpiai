"""
Subscription Models - Plan definitions and distributor subscription tracking.
Handles monthly/annual billing cycles, courtesy memberships, and access control.

Migration Path: Subscription verification will move to smart-contract-based proofs.
"""
from datetime import datetime
from enum import Enum
from extensions import db


class PlanInterval(str, Enum):
    MONTHLY = 'monthly'
    ANNUAL = 'annual'


class SubscriptionStatus(str, Enum):
    ACTIVE = 'active'
    PENDING = 'pending'
    PAST_DUE = 'past_due'
    CANCELLED = 'cancelled'
    TRIAL = 'trial'
    COURTESY = 'courtesy'


class Plan(db.Model):
    """
    Subscription plans managed by Super Admin.
    Defines pricing, features, and billing intervals.
    """
    __tablename__ = 'plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)   # e.g. "Starter", "Pro", "Enterprise"
    description = db.Column(db.Text, nullable=True)

    # Pricing
    price_monthly = db.Column(db.Float, default=0.0, nullable=False)
    price_annual = db.Column(db.Float, default=0.0, nullable=False)
    currency = db.Column(db.String(10), default='USD')

    # Limits encoded as JSON — flexible for future feature additions
    features = db.Column(db.JSON, default=lambda: {
        'max_agents': 1,
        'max_documents': 10,
        'max_leads': 100,
        'channels': ['whatsapp'],
        'rag_enabled': True,
        'analytics_enabled': False,
    })

    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)  # Auto-assigned on registration

    # dLocal Go Mapping
    dlocal_plan_id = db.Column(db.String(100), nullable=True, unique=True)
    dlocal_plan_token = db.Column(db.String(100), nullable=True, unique=True, index=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscriptions = db.relationship('Subscription', back_populates='plan', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price_monthly': self.price_monthly,
            'price_annual': self.price_annual,
            'currency': self.currency,
            'features': self.features,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Plan {self.name} ${self.price_monthly}/mo>'


class Subscription(db.Model):
    """
    Tracks a distributor's active subscription to a plan.
    One active subscription per distributor at any given time.
    """
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)

    # Tenant link
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False, index=True)
    # The relationship is defined in the Distributor model with a backref 'subscription'

    # Plan link
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    plan = db.relationship('Plan', back_populates='subscriptions')

    # Billing
    interval = db.Column(db.Enum(PlanInterval), default=PlanInterval.MONTHLY, nullable=False)
    status = db.Column(db.Enum(SubscriptionStatus), default=SubscriptionStatus.TRIAL, nullable=False)

    # Dates
    start_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)            # NULL = no expiry (courtesy)
    trial_ends_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)

    # Payment tracking
    last_payment_at = db.Column(db.DateTime, nullable=True)
    next_payment_at = db.Column(db.DateTime, nullable=True)

    # dLocal Go Mapping
    dlocal_subscription_id = db.Column(db.String(100), nullable=True, unique=True)
    dlocal_subscription_token = db.Column(db.String(100), nullable=True, unique=True, index=True)

    # Metadata
    notes = db.Column(db.Text, nullable=True)  # Super Admin can add notes (e.g. "Courtesy for beta tester")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_active(self):
        """Check if subscription grants access."""
        if self.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL, SubscriptionStatus.COURTESY):
            if self.end_date and self.end_date < datetime.utcnow():
                return False
            return True
        return False

    def to_dict(self):
        return {
            'id': self.id,
            'distributor_id': self.distributor_id,
            'plan': self.plan.to_dict() if self.plan else None,
            'interval': self.interval.value,
            'status': self.status.value,
            'is_active': self.is_active,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'trial_ends_at': self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            'next_payment_at': self.next_payment_at.isoformat() if self.next_payment_at else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Subscription dist={self.distributor_id} plan={self.plan_id} status={self.status.value}>'
