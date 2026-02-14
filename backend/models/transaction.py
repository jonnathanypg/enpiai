from datetime import datetime
from extensions import db
from enum import Enum

class TransactionStatus(str, Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    REFUNDED = 'refunded'

class TransactionType(str, Enum):
    PAYMENT = 'payment'
    REFUND = 'refund'

class Transaction(db.Model):
    """
    Log of all payment attempts and transactions processed via Rebill.
    """
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)

    # Distributor link
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False, index=True)
    distributor = db.relationship('Distributor', backref=db.backref('transactions', lazy='dynamic'))

    # Rebill Data
    rebill_id = db.Column(db.String(100), nullable=True, index=True) # Payment ID from Rebill
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD')
    status = db.Column(db.Enum(TransactionStatus), default=TransactionStatus.PENDING)
    type = db.Column(db.Enum(TransactionType), default=TransactionType.PAYMENT)

    # Metadata
    description = db.Column(db.String(255), nullable=True)
    failure_reason = db.Column(db.String(255), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'distributor_id': self.distributor_id,
            'rebill_id': self.rebill_id,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status.value,
            'type': self.type.value,
            'description': self.description,
            'failure_reason': self.failure_reason,
            'created_at': self.created_at.isoformat()
        }
