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


def extract_text_from_pdf(filepath):
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
    return text


@rag_bp.route('', methods=['GET'])
@jwt_required()
def list_documents():
    """
    List RAG documents.
    - Super Admin: lists global docs (distributor_id IS NULL)
    - Distributor: lists their own docs
    """
    db.session.rollback()

    try:
        user = _get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if user.role == UserRole.SUPER_ADMIN:
            docs = Document.query.filter(
                Document.distributor_id.is_(None)
            ).order_by(Document.created_at.desc()).all()
        else:
            if not user.distributor_id:
                return jsonify({'error': 'Distributor not found'}), 404
            docs = Document.query.filter_by(
                distributor_id=user.distributor_id
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
    - Super Admin: saved as global doc (distributor_id=None, namespace="global")
    - Distributor: saved under their own tenant
    
    IMPORTANT: Text extraction (especially PDF) can take 30+ seconds.
    We MUST release the DB connection before extraction to prevent
    'MySQL server has gone away' errors on remote databases.
    """
    db.session.rollback()

    try:
        # ── Step 1: Authenticate & extract user info into Python primitives ──
        user = _get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        is_super_admin = user.role == UserRole.SUPER_ADMIN
        distributor_id = None if is_super_admin else user.distributor_id

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

        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        original_filename = file.filename

        # ── Step 3: Save file to disk ──
        folder_name = 'global' if is_super_admin else f'dist_{distributor_id}'
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], folder_name)
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

        # ── Step 4: RELEASE the DB connection before the slow extraction ──
        # This is critical: close the session so the connection returns to the pool.
        # Without this, MySQL kills our idle connection during the 30+ second extraction.
        db.session.remove()

        # ── Step 5: Extract text (SLOW — no DB connection held) ──
        text_content = ""
        if file_ext == 'pdf':
            text_content = extract_text_from_pdf(filepath)
        elif file_ext in ['txt', 'md']:
            with open(filepath, 'r', encoding='utf-8') as f:
                text_content = f.read()

        if not text_content:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': 'Could not extract text from file'}), 400

        # Chunking (Simple)
        chunk_size = 1000
        chunks = [text_content[i:i+chunk_size] for i in range(0, len(text_content), chunk_size)]

        # ── Step 6: Get a FRESH DB connection (pool_pre_ping ensures it's alive) ──
        doc = Document(
            distributor_id=distributor_id,
            filename=filename,
            original_filename=original_filename,
            file_type=file_ext,
            file_size=os.path.getsize(filepath),
            file_path=filepath,
            is_processed=False,
            chunk_count=len(chunks)
        )
        db.session.add(doc)
        db.session.commit()

        # ── Step 7: Dispatch to RAG Service (async via Celery) ──
        rag_service.upsert_document_async(
            text_chunks=chunks,
            distributor_id=distributor_id,
            document_id=doc.id,
            metadata={'filename': filename, 'type': file_ext}
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
