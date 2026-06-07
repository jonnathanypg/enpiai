"""
Celery Tasks - Background task definitions for heavy operations.
These tasks run in the Celery worker, not in the Flask web process.

Usage:
    # Start worker:
    celery -A celery_app.celery worker --loglevel=info

Migration Path: Tasks will be distributed across a P2P mesh.
"""
import sys
import os
import logging
from celery_app import celery

# Ensure current directory is in sys.path for Celery workers
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_pdf_report(self, distributor_id, report_type, data):
    """
    Generate a PDF report in the background.
    Replaces the ThreadPoolExecutor pattern for PDF generation.
    """
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from extensions import db as task_db
            task_db.session.rollback()
            from services.pdf_service import pdf_service
            result = pdf_service.generate_report(distributor_id, report_type, data)
            logger.info(f"PDF report generated for distributor {distributor_id}")
            return {'status': 'success', 'path': result}
    except Exception as exc:
        logger.error(f"PDF generation failed: {exc}")
        raise self.retry(exc=exc)


@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def index_document_rag(self, filepath, distributor_id, document_id, metadata=None):
    """
    Index document into Pinecone in the background.
    Extracts text, chunks it, and vectorizes.
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
                                text_content += page_text + "\\n"
                except Exception as e:
                    logger.error(f"PDF extraction error in worker: {e}")
            elif file_ext in ['txt', 'md', 'csv']:
                with open(filepath, 'r', encoding='utf-8') as f:
                    text_content = f.read()

            if not text_content:
                logger.warning(f"Could not extract text from {filepath}")
                # We should still mark it as processed but empty, or keep it unprocessed?
                # Better to mark it as processed with 0 chunks to avoid being stuck.
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
            text_chunks = text_splitter.split_text(text_content)

            # 3. Vectorize and Upsert
            vector_ids = rag_service.upsert_document(
                text_chunks=text_chunks,
                distributor_id=distributor_id,
                document_id=document_id,
                metadata=metadata
            )

            # 4. Mark document as processed and save metadata in the database
            task_db.session.rollback()
            doc = Document.query.get(document_id)
            if doc:
                doc.is_processed = True
                doc.chunk_count = len(vector_ids)
                doc.pinecone_ids = vector_ids
                task_db.session.commit()
                logger.info(f"Document {document_id} marked as processed with {len(vector_ids)} chunks")

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
                except Exception as e:
                    logger.warning(f"Broadcast send error to {recipient}: {e}")
                    errors += 1

            logger.info(f"Broadcast complete: {sent} sent, {errors} errors")
            return {'status': 'success', 'sent': sent, 'errors': errors}
    except Exception as exc:
        logger.error(f"Broadcast failed: {exc}")
        raise self.retry(exc=exc)


@celery.task(bind=True, max_retries=2, default_retry_delay=5)
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
            from datetime import datetime
            from extensions import db as task_db
            from models.distributor import Distributor
            from models.conversation import Conversation, Message, MessageRole
            from services.agent_orchestrator import get_agent_orchestrator

            task_db.session.rollback()

            distributor = Distributor.query.get(distributor_id)
            conversation = Conversation.query.get(conversation_id)

            if not distributor or not conversation:
                logger.error(f"Webhook task: Distributor {distributor_id} or Conversation {conversation_id} not found")
                return {'status': 'error', 'reason': 'not_found'}

            # Close transaction before long-running agent call to prevent stale connections
            task_db.session.rollback()

            # Run agent
            orchestrator = get_agent_orchestrator(distributor)
            response_data = orchestrator.process_message(
                conversation=conversation,
                user_message=message_text,
                channel=channel
            )

            ai_reply_text = response_data.get('content')
            logger.info(f"[TASKS] AI response content received: '{ai_reply_text}'")
            
            if ai_reply_text:
                # Re-fetch or refresh session before commit to avoid "MySQL server has gone away" 
                # after long LLM wait.
                task_db.session.rollback()
                conversation = Conversation.query.get(conversation_id)
                
                # Save AI response
                ai_msg = Message(
                    conversation_id=conversation.id,
                    role=MessageRole.ASSISTANT,
                    content=ai_reply_text,
                    message_metadata={'agent_name': response_data.get('agent_name')}
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
                    if is_audio:
                        try:
                            import uuid
                            import re
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
            
            # Final cleanup inside the context to prevent teardown from failing on stale connections
            try:
                task_db.session.rollback()
                task_db.session.remove()
            except Exception as e:
                logger.debug(f"Task cleanup error (non-critical): {e}")
            
            return {'status': 'success', 'reply_sent': bool(ai_reply_text)}

    except Exception as exc:
        logger.error(f"Webhook task failed: {exc}")
        # Ensure session is cleaned up on error
        try:
            from extensions import db as task_db
            task_db.session.remove()
        except Exception as e:
            logger.debug(f"Task cleanup error on exception: {e}")
        raise self.retry(exc=exc)
    finally:
        # Cleanup connection pool
        try:
            from extensions import db as task_db
            task_db.session.remove()
        except Exception as e:
            logger.debug(f"Task cleanup error in finally: {e}")


@celery.task(bind=True, max_retries=2, default_retry_delay=30)
def process_wellness_evaluation(self, evaluation_id, distributor_id, data=None):
    """
    Process the complete wellness evaluation flow in the background:
    1. AI Diagnosis & Recommendations
    2. PDF Generation
    3. Messaging (Email + WhatsApp)
    """
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from extensions import db as task_db
            from models.wellness_evaluation import WellnessEvaluation
            from models.distributor import Distributor
            from models.lead import Lead
            from services.ai_diagnostic_service import generate_diagnosis
            from services.pdf_service import pdf_service
            from services.email_service import email_service
            from services.messaging_service import messaging_service
            from flask import current_app

            task_db.session.rollback()
            
            evaluation = WellnessEvaluation.query.get(evaluation_id)
            distributor = Distributor.query.get(distributor_id)
            
            if not evaluation or not distributor:
                logger.error(f"Wellness Task: Evaluation {evaluation_id} or Distributor {distributor_id} not found")
                return {'status': 'error', 'reason': 'not_found'}

            # 1. AI Diagnosis
            try:
                lang = evaluation.language or distributor.language or 'es'
                ai_result = generate_diagnosis(
                    age=evaluation.age or 0,
                    weight_kg=evaluation.weight_kg or 0,
                    height_cm=evaluation.height_cm or 0,
                    blood_pressure=evaluation.blood_pressure or 'N/A',
                    pulse=evaluation.pulse or 72,
                    energy_level=evaluation.energy_level or 5,
                    symptoms=evaluation.symptoms,
                    observations=evaluation.observations or '',
                    language=lang,
                    activity_level=evaluation.activity_level,
                    exercise_frequency=evaluation.exercise_frequency,
                    meals_per_day=evaluation.meals_per_day,
                    water_intake_liters=evaluation.water_intake_liters,
                    sleep_hours=evaluation.sleep_hours,
                    sleep_quality=evaluation.sleep_quality,
                )
                
                # Re-fetch evaluation after AI call
                task_db.session.rollback()
                evaluation = WellnessEvaluation.query.get(evaluation_id)
                evaluation.diagnosis = ai_result.get('diagnosis', '')
                evaluation.recommendations = ai_result.get('recommendations', '')
                task_db.session.commit()
                logger.info(f"AI results saved for evaluation {evaluation.id}")
            except Exception as ai_err:
                logger.error(f"AI diagnosis generation failed in worker: {ai_err}")

            # 2. PDF Generation
            pdf_url = None
            filename = None
            pdf_path = None
            try:
                pdf_path = pdf_service.generate_wellness_report(evaluation, distributor)
                if pdf_path:
                    filename = os.path.basename(pdf_path)
                    evaluation.pdf_report_path = filename
                    task_db.session.commit()
                    
                    api_base = current_app.config.get('API_BASE_URL', 'http://localhost:5000')
                    pdf_url = f"{api_base}/api/wellness/reports/{filename}"
            except Exception as pdf_err:
                logger.error(f"PDF generation failed in worker: {pdf_err}")

            # 3. Send to Lead (Email + WhatsApp)
            if evaluation.lead:
                # Email
                if evaluation.lead.email:
                    try:
                        email_service.send_wellness_report_to_lead(
                            to_email=evaluation.lead.email,
                            distributor_name=distributor.name,
                            evaluation_data=evaluation.to_dict(),
                            pdf_path=pdf_path,
                            lang=distributor.language or 'es'
                        )
                    except Exception as email_err:
                        logger.warning(f"Failed to send email to lead: {email_err}")

                # WhatsApp
                if evaluation.lead.phone:
                    try:
                        dist_link = f"https://enpi.click/evaluate/{distributor.herbalife_id or distributor.id}"
                        
                        # Localized WhatsApp Intro
                        wa_intros = {
                            'es': f"¡Hola {evaluation.lead.first_name}! 🌿 Tu análisis de bienestar está listo. Te lo adjunto a continuación para que lo revises.\n\nRealiza otra evaluación aquí: {dist_link}",
                            'en': f"Hi {evaluation.lead.first_name}! 🌿 Your wellness analysis is ready. I'm attaching it below for you to review.\n\nTake another evaluation here: {dist_link}",
                            'pt': f"Olá {evaluation.lead.first_name}! 🌿 Sua análise de bem-estar está pronta. Estou anexando-a abaixo para você revisar.\n\nFaça outra avaliação aqui: {dist_link}"
                        }
                        wa_intro = wa_intros.get(lang, wa_intros['es'])

                        messaging_service.send_whatsapp(
                            to_phone=evaluation.lead.phone,
                            message=wa_intro,
                            distributor_id=distributor.id
                        )
                        
                        if pdf_url:
                            caption_map = {
                                'es': f"Evaluación de Bienestar - {evaluation.lead.first_name}",
                                'en': f"Wellness Evaluation - {evaluation.lead.first_name}",
                                'pt': f"Avaliação de Bem-estar - {evaluation.lead.first_name}"
                            }
                            messaging_service.send_whatsapp_media(
                                to_phone=evaluation.lead.phone,
                                media_url=pdf_url,
                                media_type="document",
                                caption=caption_map.get(lang, caption_map['es']),
                                file_name=filename,
                                distributor_id=distributor.id
                            )
                    except Exception as wa_err:
                        logger.warning(f"Failed to send WhatsApp to lead: {wa_err}")

            # 4. Notify Distributor
            try:
                distributor_phone = distributor.whatsapp_phone or distributor.phone
                lead_name = evaluation.lead.full_name if evaluation.lead else "Anónimo"
                
                if distributor_phone:
                    notification_msg = (
                        f"📝 *NUEVA EVALUACIÓN DE BIENESTAR*\n"
                        f"El prospecto *{lead_name}* ha completado su evaluación.\n\n"
                        f"📊 *Resultados:* \n"
                        f"- IMC: {evaluation.bmi:.1f}\n"
                        f"- Meta: {evaluation.primary_goal}\n"
                        f"- Motivación: {evaluation.motivation}\n\n"
                        f"El reporte PDF ya ha sido enviado al lead."
                    )
                    messaging_service.send_whatsapp(distributor_phone, notification_msg, distributor.id)

                from models.user import User
                dist_user = User.query.filter_by(distributor_id=distributor_id).first()
                if dist_user:
                    email_service.send_wellness_evaluation_notification(
                        to_email=dist_user.email,
                        distributor_name=distributor.name,
                        lead_name=lead_name,
                        bmi=str(round(evaluation.bmi, 1)) if evaluation.bmi else 'N/A',
                        goal=evaluation.primary_goal or '',
                        lang=distributor.language or 'en'
                    )
            except Exception as notify_err:
                logger.warning(f"Distributor notification failed: {notify_err}")

            return {'status': 'success', 'evaluation_id': evaluation_id}
            
    except Exception as exc:
        logger.error(f"Wellness task critical failure: {exc}")
        raise self.retry(exc=exc)
    finally:
        try:
            from extensions import db as task_db
            task_db.session.remove()
        except:
            pass


