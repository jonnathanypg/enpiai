"""
Document Model - RAG documents uploaded by distributors.
Migration Path: Document content will be encrypted. Vector embeddings are operational data
(anonymized) and can feed training pipelines.
"""
from datetime import datetime
from extensions import db


class Document(db.Model):
    """Document model — files uploaded for RAG knowledge base"""
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False, index=True)

    # File info
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # pdf, docx, txt, xlsx, csv
    file_size = db.Column(db.Integer, nullable=True)  # bytes
    file_path = db.Column(db.String(500), nullable=True)

    # RAG metadata
    pinecone_ids = db.Column(db.JSON, default=list)  # List of vector IDs in Pinecone
    chunk_count = db.Column(db.Integer, default=0)
    is_processed = db.Column(db.Boolean, default=False)

    # Description
    description = db.Column(db.Text, nullable=True)
    tags = db.Column(db.JSON, default=list)

    # Relationships
    distributor = db.relationship('Distributor', back_populates='documents')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'distributor_id': self.distributor_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'chunk_count': self.chunk_count,
            'is_processed': self.is_processed,
            'description': self.description,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
        }

    def __repr__(self):
        return f'<Document {self.filename}>'
