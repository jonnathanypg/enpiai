"""
Note Model - Stores annotations for Leads and Customers.
"""
from datetime import datetime
from extensions import db

class Note(db.Model):
    """Internal notes for CRM contacts"""
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False, index=True)
    
    # Link to either lead or customer
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True, index=True)
    
    # Content
    content = db.Column(db.Text, nullable=False)
    
    # Metadata
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Who wrote it
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    author = db.relationship('User', foreign_keys=[author_id])
    lead = db.relationship('Lead', back_populates='note_records')
    customer = db.relationship('Customer', back_populates='note_records')

    def to_dict(self):
        return {
            'id': self.id,
            'distributor_id': self.distributor_id,
            'lead_id': self.lead_id,
            'customer_id': self.customer_id,
            'content': self.content,
            'author_id': self.author_id,
            'author_name': self.author.name if self.author else "System",
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
