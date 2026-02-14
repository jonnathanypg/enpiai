"""
RAG Routes - Document Management for Distributors.
Handles file uploads, text extraction, and vectorization.
"""
import os
import logging
import pdfplumber
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models.user import User
from models.document import Document
from services.rag_service import rag_service

logger = logging.getLogger(__name__)

rag_bp = Blueprint('rag', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md'}

def _get_distributor_id():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    return user.distributor_id if user else None

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
    """List all RAG documents for the distributor"""
    db.session.rollback()
    
    try:
        distributor_id = _get_distributor_id()
        if not distributor_id:
            return jsonify({'error': 'Distributor not found'}), 404

        docs = Document.query.filter_by(distributor_id=distributor_id).order_by(Document.created_at.desc()).all()
        return jsonify({'data': [d.to_dict() for d in docs]}), 200

    except Exception as e:
        logger.error(f"List documents error: {e}")
        return jsonify({'error': str(e)}), 500

@rag_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_document():
    """Upload and process a document"""
    db.session.rollback()
    
    try:
        distributor_id = _get_distributor_id()
        if not distributor_id:
            return jsonify({'error': 'Distributor not found'}), 404

        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower()
            
            # Save file
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], f'dist_{distributor_id}')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            
            # Create DB record
            doc = Document(
                distributor_id=distributor_id,
                filename=filename,
                original_filename=file.filename,
                file_type=file_ext,
                file_size=os.path.getsize(filepath),
                file_path=filepath,
                is_processed=False
            )
            db.session.add(doc)
            db.session.flush() # Get ID
            
            # Extract text
            text_content = ""
            if file_ext == 'pdf':
                text_content = extract_text_from_pdf(filepath)
            elif file_ext in ['txt', 'md']:
                with open(filepath, 'r', encoding='utf-8') as f:
                    text_content = f.read()
            
            if not text_content:
                 db.session.rollback()
                 return jsonify({'error': 'Could not extract text from file'}), 400
                 
            # Chunking (Simple)
            chunk_size = 1000
            chunks = [text_content[i:i+chunk_size] for i in range(0, len(text_content), chunk_size)]
            doc.chunk_count = len(chunks)
            db.session.commit()
            
            # Dispatch to RAG Service (Async preferably)
            # For now, calling the sync wrapper or async if configured
            # rag_service.upsert_document_async needs 'tasks' module which might cause circular imports if not careful
            # We'll use the service method which handles the import internally
            rag_service.upsert_document_async(
                text_chunks=chunks,
                distributor_id=distributor_id,
                document_id=doc.id,
                metadata={'filename': filename, 'type': file_ext}
            )
            
            # We can mark as processed immediately if sync, or wait for webhook/polling
            # Since upsert_document_async might fall back to sync, let's just return accepted
            
            return jsonify({'data': doc.to_dict(), 'message': 'File uploaded and processing started'}), 202
            
        else:
            return jsonify({'error': 'File type not allowed'}), 400

    except Exception as e:
        db.session.rollback()
        logger.error(f"Upload document error: {e}")
        return jsonify({'error': str(e)}), 500

@rag_bp.route('/<int:doc_id>', methods=['DELETE'])
@jwt_required()
def delete_document(doc_id):
    """Delete a document"""
    db.session.rollback()
    
    try:
        distributor_id = _get_distributor_id()
        doc = Document.query.filter_by(id=doc_id, distributor_id=distributor_id).first()
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
            
        # TODO: Delete from Pinecone (Service needed)
        # rag_service.delete_document(doc_id)
        
        # Delete file
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
            
        db.session.delete(doc)
        db.session.commit()
        
        return jsonify({'message': 'Document deleted'}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete document error: {e}")
        return jsonify({'error': str(e)}), 500
