"""
Product Model - Herbalife product catalog per distributor.
Migration Path: Product data is operational (non-PII), can be anonymized for training.
"""
from datetime import datetime
from extensions import db


class Product(db.Model):
    """Product model — Herbalife product catalog managed per distributor"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False, index=True)

    # Product Info
    name = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(100), nullable=True)  # e.g., "Nutrición", "Control de peso", "Energía"
    description = db.Column(db.Text, nullable=True)

    # Pricing
    price = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(10), default='USD')

    # Media
    image_url = db.Column(db.String(500), nullable=True)

    # Inventory (optional)
    stock_quantity = db.Column(db.Integer, nullable=True)
    is_available = db.Column(db.Boolean, default=True)

    # Benefits & ingredients (for RAG / agent knowledge)
    benefits = db.Column(db.JSON, default=list)      # e.g., ["Energy", "Weight management"]
    ingredients = db.Column(db.Text, nullable=True)
    usage_instructions = db.Column(db.Text, nullable=True)

    # Relationships
    distributor = db.relationship('Distributor', back_populates='products')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'distributor_id': self.distributor_id,
            'name': self.name,
            'sku': self.sku,
            'category': self.category,
            'description': self.description,
            'price': self.price,
            'currency': self.currency,
            'image_url': self.image_url,
            'stock_quantity': self.stock_quantity,
            'is_available': self.is_available,
            'benefits': self.benefits,
            'ingredients': self.ingredients,
            'usage_instructions': self.usage_instructions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Product {self.name}>'
