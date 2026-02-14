"""
Channel Model - Communication channel configurations per distributor.
Migration Path: Channel credentials will be stored in client-side encrypted vaults.
"""
from datetime import datetime
from enum import Enum
from extensions import db
from services.encryption_service import EncryptedJSON


class ChannelType(str, Enum):
    WHATSAPP = 'whatsapp'
    TELEGRAM = 'telegram'
    EMAIL = 'email'
    WEBCHAT = 'webchat'


class ChannelStatus(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    CONNECTING = 'connecting'
    ERROR = 'error'


class Channel(db.Model):
    """Channel model — communication channel config per distributor"""
    __tablename__ = 'channels'

    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False, index=True)

    # Channel info
    channel_type = db.Column(db.Enum(ChannelType), nullable=False)
    name = db.Column(db.String(255), nullable=False)

    # Status
    status = db.Column(db.Enum(ChannelStatus), default=ChannelStatus.INACTIVE)

    # Configuration (channel-specific settings stored as JSON)
    # WhatsApp: { phone_number, session_id, qr_code }
    # Telegram: { bot_token, bot_username }
    # Email: { smtp_host, smtp_port, smtp_user }
    # WebChat: { widget_key, allowed_domains }
    config = db.Column(db.JSON, default=dict)

    # Credentials (encrypted at rest — Sovereign SQL Layer)
    credentials = db.Column(EncryptedJSON, nullable=True)

    # Relationships
    distributor = db.relationship('Distributor', back_populates='channels')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_connected_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self, include_credentials=False):
        data = {
            'id': self.id,
            'distributor_id': self.distributor_id,
            'channel_type': self.channel_type.value,
            'name': self.name,
            'status': self.status.value,
            'config': self.config,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_connected_at': self.last_connected_at.isoformat() if self.last_connected_at else None,
        }
        if include_credentials:
            data['credentials'] = self.credentials
        return data

    def __repr__(self):
        return f'<Channel {self.name} ({self.channel_type.value})>'
