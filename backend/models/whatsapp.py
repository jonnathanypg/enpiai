from datetime import datetime
from extensions import db

class BaileySession(db.Model):
    """
    Model for WhatsApp sessions managed by api-whatsapp (Baileys).
    Migration Path: WhatsApp sessions will move to a decentralized state via DID-based identity.
    """
    __tablename__ = 'bailey_sessions'

    pk_id = db.Column(db.String(255), primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'pk_id': self.pk_id,
            'session_id': self.session_id,
            'data': self.data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
