"""
RAG Routes - Document Management for Distributors and Super Admin.
Handles file uploads, text extraction, and vectorization.

Super Admin uploads go to a "global" namespace accessible by all agents.
Distributor uploads go to their own "dist_{id}" namespace.
"""
import os
import logging
import pdfplumber
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models.user import User, UserRole
from models.document import Document
from services.rag_service import rag_service

logger = logging.getLogger(__name__)

rag_bp = Blueprint('rag', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md'}


def _get_current_user():
    """Return the current User object."""
    user_id = get_jwt_identity()
    return User.query.get(int(user_id))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@rag_bp.route('', methods=['GET'])
@jwt_required()
def list_documents():
    """
    List RAG documents.
    - Super Admin: lists global docs (distributor_id IS NULL) or specific distributor docs via header.
    - Distributor: lists their own docs.
    """
    db.session.rollback()

    try:
        user = _get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        distributor_id = user.distributor_id
        is_super_admin = user.role == UserRole.SUPER_ADMIN
        
        # Super Admin Override
        if is_super_admin:
            override_id = request.headers.get('X-Distributor-Id')
            if override_id:
                distributor_id = int(override_id)
            else:
                # Default Super Admin behavior: global docs
                docs = Document.query.filter(
                    Document.distributor_id.is_(None)
                ).order_by(Document.created_at.desc()).all()
                return jsonify({'data': [d.to_dict() for d in docs]}), 200

        # Normal or Overridden flow
        if not distributor_id:
            return jsonify({'error': 'Distributor not found'}), 404
            
        docs = Document.query.filter_by(
            distributor_id=distributor_id
        ).order_by(Document.created_at.desc()).all()

        return jsonify({'data': [d.to_dict() for d in docs]}), 200

    except Exception as e:
        logger.error(f"List documents error: {e}")
        return jsonify({'error': str(e)}), 500


@rag_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_document():
    """
    Upload and process a document.
    - Super Admin: global doc or specific distributor doc via header.
    - Distributor: saved under their own tenant.
    """
    db.session.rollback()

    try:
        import uuid
        user = _get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        is_super_admin = user.role == UserRole.SUPER_ADMIN
        distributor_id = user.distributor_id
        
        # Super Admin Override
        if is_super_admin:
            override_id = request.headers.get('X-Distributor-Id')
            if override_id:
                distributor_id = int(override_id)
            else:
                distributor_id = None # Global doc

        if not is_super_admin and not distributor_id:
            return jsonify({'error': 'Distributor not found'}), 404

        # ── Step 2: Validate request ──
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if not (file and allowed_file(file.filename)):
            return jsonify({'error': 'File type not allowed'}), 400

        original_filename = file.filename
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        
        # Generate unique filename to prevent overwrites
        safe_name = secure_filename(original_filename)
        filename = f"{uuid.uuid4().hex}_{safe_name}"

        # ── Step 3: Save file to disk ──
        folder_name = 'global' if is_super_admin else f'dist_{distributor_id}'
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], folder_name)
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

        # ── Step 4: Create Document Record (Unprocessed) ──
        doc = Document(
            distributor_id=distributor_id,
            filename=filename,
            original_filename=original_filename,
            file_type=file_ext,
            file_size=os.path.getsize(filepath),
            file_path=filepath,
            is_processed=False,
            chunk_count=0
        )
        db.session.add(doc)
        db.session.commit()

        # ── Step 5: Dispatch to RAG Service (async via Celery) ──
        # We pass the filepath instead of extracted chunks
        from tasks import index_document_rag
        index_document_rag.delay(
            filepath=filepath,
            distributor_id=distributor_id,
            document_id=doc.id,
            metadata={'filename': original_filename, 'type': file_ext}
        )

        return jsonify({'data': doc.to_dict(), 'message': 'File uploaded and processing started'}), 202

    except Exception as e:
        db.session.rollback()
        logger.error(f"Upload document error: {e}")
        return jsonify({'error': str(e)}), 500


@rag_bp.route('/<int:doc_id>', methods=['DELETE'])
@jwt_required()
def delete_document(doc_id):
    """Delete a document (respects tenant isolation)"""
    db.session.rollback()

    try:
        user = _get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        is_super_admin = user.role == UserRole.SUPER_ADMIN

        if is_super_admin:
            doc = Document.query.filter_by(id=doc_id, distributor_id=None).first()
        else:
            doc = Document.query.filter_by(id=doc_id, distributor_id=user.distributor_id).first()

        if not doc:
            return jsonify({'error': 'Document not found'}), 404

        # Delete vectors from Pinecone FIRST
        try:
            rag_service.delete_document_vectors(doc.id, doc.distributor_id)
        except Exception as e:
            logger.warning(f"Pinecone vector deletion failed for doc {doc_id}: {e}")

        # Delete file from disk
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)

        db.session.delete(doc)
        db.session.commit()

        return jsonify({'message': 'Document deleted'}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete document error: {e}")
        return jsonify({'error': str(e)}), 500
