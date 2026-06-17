"""
Celery tasks for background processing (IAGS Protocol).
Includes PDF generation, RAG indexing, and webhook processing.

Copyright © 2026 WEBLIFETECH (Jonnathan Peña). All Rights Reserved.
"""
import os
import logging
import time
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask import current_app

from celery_app import celery
from extensions import db
from models.distributor import Distributor
from models.conversation import Conversation, ConversationChannel, ConversationStatus, Message, MessageRole

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=2, default_retry_delay=10)
def generate_pdf_report(self, distributor_id, report_type, data):
    """
    Generate a wellness report PDF in the background.
    """
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from services.pdf_service import PDFService
            from models.distributor import Distributor
            
            distributor = Distributor.query.get(distributor_id)
            if not distributor:
                return {'status': 'error', 'reason': 'distributor_not_found'}

            logger.info(f"Generating {report_type} report for distributor {distributor_id}")
            result = PDFService.generate_wellness_report(distributor, data)
            
            return {'status': 'success', 'path': result}
    except Exception as exc:
        logger.error(f"PDF generation failed: {exc}")
        raise self.retry(exc=exc)


@celery.task(bind=True, max_retries=3, default_retry_delay=20)
def index_document_rag(self, filepath, distributor_id, document_id, metadata=None):
    """
    Process a document and index its chunks in Pinecone.
    """
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from extensions import db as task_db
            task_db.session.rollback()
            from services.rag_service import rag_service
            from models.document import Document
            import os
            import pdfplumber
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            # 1. Read file and extract text
            text_content = ""
            file_ext = metadata.get('type', 'txt') if metadata else 'txt'
            
            if not os.path.exists(filepath):
                logger.error(f"File not found for indexing: {filepath}")
                return {'status': 'error', 'reason': 'file_not_found'}

            if file_ext == 'pdf':
                try:
                    with pdfplumber.open(filepath) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text_content += page_text + "\n"
                except Exception as e:
                    logger.error(f"PDF extraction error in worker: {e}")
            elif file_ext in ['txt', 'md', 'csv']:
                with open(filepath, 'r', encoding='utf-8') as f:
                    text_content = f.read()

            if not text_content:
                logger.warning(f"Could not extract text from {filepath}")
                task_db.session.rollback()
                doc = Document.query.get(document_id)
                if doc:
                    doc.is_processed = True
                    doc.chunk_count = 0
                    task_db.session.commit()
                return {'status': 'error', 'reason': 'empty_text'}

            # 2. Chunking with RecursiveCharacterTextSplitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                is_separator_regex=False,
            )
            chunks = text_splitter.split_text(text_content)

            # 3. Upsert to Pinecone
            vector_ids = rag_service.upsert_document(
                text_chunks=chunks,
                distributor_id=distributor_id,
                document_id=document_id,
                metadata=metadata
            )

            # 4. Update Document model
            task_db.session.rollback()
            doc = Document.query.get(document_id)
            if doc:
                doc.pinecone_ids = vector_ids
                doc.chunk_count = len(vector_ids)
                doc.is_processed = True
                doc.processed_at = datetime.utcnow()
                task_db.session.commit()

            logger.info(f"Document {document_id} indexed: {len(vector_ids)} chunks")
            return {'status': 'success', 'chunks': len(vector_ids)}
    except Exception as exc:
        logger.error(f"RAG indexing failed: {exc}")
        raise self.retry(exc=exc)


@celery.task(bind=True, max_retries=2, default_retry_delay=10)
def send_broadcast_message(self, distributor_id, channel, recipients, message):
    """
    Send a broadcast message to multiple recipients in the background.
    Useful for campaigns and bulk notifications.
    """
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from extensions import db as task_db
            task_db.session.rollback()
            from services.messaging_service import messaging_service
            
            sent = 0
            errors = 0
            
            for recipient in recipients:
                try:
                    messaging_service.send_message(
                        channel=channel,
                        to=recipient,
                        message=message,
                        distributor_id=distributor_id
                    )
                    sent += 1
                    time.sleep(0.5) # FIX-015: Add delay to avoid rate limiting
                except Exception as e:
                    logger.warning(f"Broadcast send error to {recipient}: {e}")
                    errors += 1

            logger.info(f"Broadcast complete: {sent} sent, {errors} errors")
            return {'status': 'success', 'sent': sent, 'errors': errors}
    except Exception as exc:
        logger.error(f"Broadcast failed: {exc}")
        raise self.retry(exc=exc)


@celery.task(bind=True, max_retries=2, default_retry_delay=5, soft_time_limit=60)
def process_webhook_message(self, distributor_id, conversation_id, message_text, channel, sender_phone=None, chat_id=None, is_audio=False):
    """
    Process incoming webhook messages with AI agent in the background.
    Called by the Fire & Forget webhook pattern.

    This task:
    1. Loads the distributor + conversation from DB
    2. Runs the agent orchestrator
    3. Saves the AI reply
    4. Sends the reply back via the messaging service (with optional voice synthesis)
    """
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from extensions import db as task_db
            task_db.session.rollback()
            from models.distributor import Distributor
            from models.conversation import Conversation
            from services.agent_orchestrator import get_agent_orchestrator

            # 1. Load context
            distributor = Distributor.query.get(distributor_id)
            conversation = Conversation.query.get(conversation_id)

            if not distributor or not conversation:
                logger.error(f"Context missing: distributor={distributor_id}, conversation={conversation_id}")
                return {'status': 'error', 'reason': 'context_missing'}

            # 2. Run Agent
            orchestrator = get_agent_orchestrator(distributor)
            response = orchestrator.process_message(
                conversation=conversation,
                user_message=message_text,
                channel=channel
            )

            ai_reply_text = response.get('content')
            if ai_reply_text:
                # Save AI Message
                ai_msg = Message(
                    conversation_id=conversation.id,
                    role=MessageRole.ASSISTANT,
                    content=ai_reply_text,
                    message_metadata={'agent_name': response.get('agent_name')}
                )
                task_db.session.add(ai_msg)
                conversation.last_message_at = datetime.utcnow()
                task_db.session.commit()

                # Send reply via messaging service
                from services.messaging_service import messaging_service
                if channel == 'whatsapp' and sender_phone:
                    # Always send text transcription
                    messaging_service.send_whatsapp(
                        to_phone=sender_phone,
                        message=ai_reply_text,
                        distributor_id=distributor_id
                    )

                    # Synthesize and send audio response if input was audio
                    # TEMPORARILY DISABLED (Voice Speaker Hidden)
                    if False: # is_audio:
                        try:
                            import uuid
                            from services.voice_service import VoiceService

                            voice_name = VoiceService.resolve_voice(distributor)
                            filename = f"reply_{uuid.uuid4().hex}.mp3"
                            voice_dir = os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads'), 'voice')
                            os.makedirs(voice_dir, exist_ok=True)
                            output_path = os.path.join(voice_dir, filename)

                            # Remove markdown formatting for cleaner neural voice output
                            clean_text = re.sub(r'[*_`#~-]', '', ai_reply_text)
                            logger.info(f"Synthesizing voice response for WhatsApp: '{clean_text[:50]}...' using '{voice_name}'")

                            if VoiceService.synthesize(clean_text, voice_name, output_path):
                                api_base = app.config.get('API_BASE_URL', 'http://localhost:5000')
                                media_url = f"{api_base}/api/voice/file/{filename}"
                                logger.info(f"Voice note synthesized successfully. Dispatching media URL: {media_url}")
                                messaging_service.send_whatsapp_media(
                                    to_phone=sender_phone,
                                    media_url=media_url,
                                    media_type="audio",
                                    distributor_id=distributor_id,
                                    file_name=filename
                                )
                            else:
                                logger.error("Voice synthesis failed during task execution.")
                        except Exception as voice_err:
                            logger.error(f"Error handling WhatsApp audio synthesis/dispatch: {voice_err}")
                elif channel == 'telegram' and chat_id:
                    messaging_service.send_telegram(
                        chat_id=chat_id,
                        message=ai_reply_text
                    )

            logger.info(f"Webhook task completed: conv={conversation_id}, reply_sent={bool(ai_reply_text)}")
            return {'status': 'success', 'reply_sent': bool(ai_reply_text)}

    except Exception as exc:
        logger.error(f"Webhook task failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        # Cleanup connection pool
        try:
            from extensions import db as task_db
            task_db.session.rollback()
            task_db.session.remove()
        except Exception as e:
            logger.debug(f"Task cleanup error in finally: {e}")


@celery.task
def cleanup_old_voice_files(days=1):
    """
    Periodic task to clean up old synthesized voice files from uploads/voice/
    """
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            voice_dir = os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads'), 'voice')
            if not os.path.exists(voice_dir):
                return {'status': 'ignored', 'reason': 'dir_not_found'}

            now = time.time()
            cutoff = now - (days * 86400)
            deleted = 0

            for f in os.listdir(voice_dir):
                file_path = os.path.join(voice_dir, f)
                if os.path.isfile(file_path):
                    if os.path.getmtime(file_path) < cutoff:
                        os.remove(file_path)
                        deleted += 1

            logger.info(f"Cleanup complete: Deleted {deleted} old voice files.")
            return {'status': 'success', 'deleted': deleted}
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {'status': 'error', 'error': str(e)}


@celery.task(bind=True, max_retries=2, default_retry_delay=30)
def process_wellness_evaluation(self, evaluation_id, distributor_id, data=None):
    """
    Process the complete wellness evaluation flow in the background:
    1. AI Diagnosis & Recommendations
    2. PDF Generation
    3. WhatsApp/Email notification
    """
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from extensions import db as task_db
            task_db.session.rollback()
            from models.wellness_evaluation import WellnessEvaluation
            from services.ai_diagnostic_service import AIDiagnosticService
            from services.pdf_service import PDFService
            from services.messaging_service import messaging_service
            from services.email_service import email_service
            
            evaluation = WellnessEvaluation.query.get(evaluation_id)
            if not evaluation:
                return {'status': 'error', 'reason': 'evaluation_not_found'}
                
            distributor = Distributor.query.get(distributor_id)
            
            # 1. AI Diagnosis
            logger.info(f"Generating AI diagnosis for evaluation {evaluation_id}")
            diagnosis = AIDiagnosticService.generate_diagnosis(evaluation, distributor)
            evaluation.ai_diagnosis = diagnosis
            evaluation.is_processed = True
            evaluation.processed_at = datetime.utcnow()
            task_db.session.commit()
            
            # 2. PDF Generation
            logger.info(f"Generating PDF report for evaluation {evaluation_id}")
            pdf_path = PDFService.generate_wellness_report(distributor, evaluation.to_dict())
            evaluation.report_pdf_path = pdf_path
            task_db.session.commit()
            
            # 3. Notifications
            # WhatsApp
            if evaluation.lead and evaluation.lead.phone:
                try:
                    report_url = f"https://enpi.click/reports/{os.path.basename(pdf_path)}"
                    message = (
                        f"¡Hola {evaluation.lead.name}! Ya tengo lista tu Evaluación de Bienestar. "
                        f"Puedes ver el reporte completo aquí: {report_url}"
                    )
                    messaging_service.send_whatsapp(
                        to_phone=evaluation.lead.phone,
                        message=message,
                        distributor_id=distributor_id
                    )
                except Exception as wa_err:
                    logger.warning(f"WhatsApp notification failed: {wa_err}")
                    
            # Email
            if evaluation.lead and evaluation.lead.email:
                try:
                    email_service.send_wellness_report(
                        email=evaluation.lead.email,
                        name=evaluation.lead.name,
                        pdf_path=pdf_path,
                        distributor=distributor
                    )
                except Exception as mail_err:
                    logger.warning(f"Email notification failed: {mail_err}")
            
            return {'status': 'success', 'pdf': pdf_path}
            
    except Exception as exc:
        logger.error(f"Wellness processing failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        try:
            from extensions import db as task_db
            task_db.session.rollback()
            task_db.session.remove()
        except Exception as e:
            logger.debug(f"Task cleanup: {e}")
