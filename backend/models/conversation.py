"""
Conversation & Message Models - Chat history for all channels.
Supports WhatsApp, Telegram, Web Chat, and internal admin conversations.

Migration Path: Conversation data will be encrypted at rest. Anonymized transcripts
feed training pipelines. user_id nullable for virtual/anonymous users.
"""
from datetime import datetime
from enum import Enum
from extensions import db


class ConversationChannel(str, Enum):
    WHATSAPP = 'whatsapp'
    TELEGRAM = 'telegram'
    WEBCHAT = 'webchat'
    EMAIL = 'email'
    INTERNAL = 'internal'  # Admin <-> Agent


class ConversationStatus(str, Enum):
    ACTIVE = 'active'
    CLOSED = 'closed'
    ARCHIVED = 'archived'


class Conversation(db.Model):
    """Conversation model — groups messages for a session"""
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False, index=True)

    # Channel info
    channel = db.Column(db.Enum(ConversationChannel), nullable=False)
    channel_conversation_id = db.Column(db.String(255), nullable=True)  # External ID (e.g., WhatsApp chat ID)

    # Participant info (phone for WhatsApp, chat_id for Telegram, etc.)
    participant_id = db.Column(db.String(255), nullable=True, index=True)
    participant_name = db.Column(db.String(255), nullable=True)

    # Link to lead/customer (if identified)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)

    # Status
    status = db.Column(db.Enum(ConversationStatus), default=ConversationStatus.ACTIVE)

    # Context / summary
    summary = db.Column(db.Text, nullable=True)
    context = db.Column(db.JSON, default=dict)  # Agent state, flow context, etc.

    # Messages relationship
    messages = db.relationship('Message', back_populates='conversation', lazy='dynamic',
                               cascade='all, delete-orphan', order_by='Message.created_at')

    # Relationships
    distributor = db.relationship('Distributor', back_populates='conversations')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self, include_messages=False):
        data = {
            'id': self.id,
            'distributor_id': self.distributor_id,
            'channel': self.channel.value,
            'participant_id': self.participant_id,
            'participant_name': self.participant_name,
            'lead_id': self.lead_id,
            'customer_id': self.customer_id,
            'status': self.status.value,
            'summary': self.summary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None
        }
        if include_messages:
            data['messages'] = [m.to_dict() for m in self.messages.limit(100).all()]
        return data

    def __repr__(self):
        return f'<Conversation {self.id} ({self.channel.value})>'


class MessageRole(str, Enum):
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'


class Message(db.Model):
    """Individual message in a conversation"""
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False, index=True)

    # Role (who sent it)
    role = db.Column(db.Enum(MessageRole), nullable=False)

    # Content
    content = db.Column(db.Text, nullable=False)

    # Optional: user_id nullable for virtual/anonymous users (per GEMINI.md rule)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Message metadata (e.g., media attachments, tool calls, etc.)
    message_metadata = db.Column(db.JSON, nullable=True)

    # Relationships
    conversation = db.relationship('Conversation', back_populates='messages')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role.value,
            'content': self.content,
            'user_id': self.user_id,
            'metadata': self.message_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Message {self.id} ({self.role.value})>'
