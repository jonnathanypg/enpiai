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

    # Nutrition Club Preparations
    is_club_menu = db.Column(db.Boolean, default=True)
    protein_grams = db.Column(db.Float, nullable=True)          # e.g., 24.0
    calories = db.Column(db.Integer, nullable=True)             # e.g., 210
    preparation_time_min = db.Column(db.Integer, default=5)     # e.g., 5 min
    customization_options = db.Column(db.JSON, default=dict)    # e.g. {"flavors": [...], "toppings": [...], "extras": [...]}
    display_order = db.Column(db.Integer, default=0)

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
            'category': self.category or 'batidos',
            'description': self.description,
            'price': self.price,
            'currency': self.currency or 'USD',
            'image_url': self.image_url,
            'stock_quantity': self.stock_quantity,
            'is_available': self.is_available if self.is_available is not None else True,
            'is_club_menu': self.is_club_menu if self.is_club_menu is not None else True,
            'protein_grams': self.protein_grams,
            'calories': self.calories,
            'preparation_time_min': self.preparation_time_min or 5,
            'customization_options': self.customization_options or {},
            'display_order': self.display_order or 0,
            'benefits': self.benefits or [],
            'ingredients': self.ingredients,
            'usage_instructions': self.usage_instructions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Product {self.name}>'
