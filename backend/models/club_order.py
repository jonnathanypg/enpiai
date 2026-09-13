"""
Club Order Model - Records customer orders placed via the Nutrition Club microsite.
"""
from datetime import datetime
import uuid
from extensions import db


class ClubOrder(db.Model):
    """Club Order model — Orders placed by customers in the Nutrition Club microsite"""
    __tablename__ = 'club_orders'

    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False, index=True)

    # Order Identification
    order_number = db.Column(db.String(50), nullable=True, unique=True)
    
    # Customer Details
    customer_name = db.Column(db.String(255), nullable=False)
    customer_phone = db.Column(db.String(50), nullable=True)
    customer_email = db.Column(db.String(255), nullable=True)
    
    # Delivery Type: dine_in (Consumo en Club), pickup (Para llevar), delivery (A domicilio)
    delivery_type = db.Column(db.String(50), default='dine_in')
    
    # Order Contents (JSON list of items with selected flavors, toppings, notes)
    items = db.Column(db.JSON, nullable=False, default=list)
    
    # Pricing
    subtotal = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(10), default='USD')
    
    # Customer Notes / Special instructions
    notes = db.Column(db.Text, nullable=True)
    
    # Status: pending, confirmed, preparing, ready, delivered, cancelled
    status = db.Column(db.String(50), default='pending')

    # Relationships
    distributor = db.relationship('Distributor', back_populates='club_orders')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def generate_order_number(self):
        """Generate a human-readable order code e.g. CN-0831-A1B2"""
        today_str = datetime.utcnow().strftime('%m%d')
        suffix = uuid.uuid4().hex[:4].upper()
        self.order_number = f"CN-{today_str}-{suffix}"
        return self.order_number

    def to_dict(self):
        return {
            'id': self.id,
            'distributor_id': self.distributor_id,
            'order_number': self.order_number,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'customer_email': self.customer_email,
            'delivery_type': self.delivery_type,
            'items': self.items or [],
            'subtotal': self.subtotal,
            'total': self.total,
            'currency': self.currency or 'USD',
            'notes': self.notes,
            'status': self.status or 'pending',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<ClubOrder {self.order_number or self.id} - {self.customer_name}>'
