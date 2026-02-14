"""
Celery Tasks - Background task definitions for heavy operations.
These tasks run in the Celery worker, not in the Flask web process.

Usage:
    # Start worker:
    celery -A celery_app.celery worker --loglevel=info

Migration Path: Tasks will be distributed across a P2P mesh.
"""
import logging
from celery_app import celery

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
            from services.pdf_service import pdf_service
            result = pdf_service.generate_report(distributor_id, report_type, data)
            logger.info(f"PDF report generated for distributor {distributor_id}")
            return {'status': 'success', 'path': result}
    except Exception as exc:
        logger.error(f"PDF generation failed: {exc}")
        raise self.retry(exc=exc)


@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def index_document_rag(self, text_chunks, distributor_id, document_id, metadata=None):
    """
    Index document chunks into Pinecone in the background.
    Replaces rag_service.upsert_document_async() ThreadPool pattern.
    """
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from services.rag_service import rag_service
            vector_ids = rag_service.upsert_document(
                text_chunks=text_chunks,
                distributor_id=distributor_id,
                document_id=document_id,
                metadata=metadata
            )
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
def process_webhook_message(self, distributor_id, conversation_id, message_text, channel, sender_phone=None, chat_id=None):
    """
    Process incoming webhook messages with AI agent in the background.
    Called by the Fire & Forget webhook pattern.

    This task:
    1. Loads the distributor + conversation from DB
    2. Runs the agent orchestrator
    3. Saves the AI reply
    4. Sends the reply back via the messaging service
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

            # Run agent
            orchestrator = get_agent_orchestrator(distributor)
            response_data = orchestrator.process_message(
                conversation=conversation,
                user_message=message_text,
                channel=channel
            )

            ai_reply_text = response_data.get('content')
            if ai_reply_text:
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
                    messaging_service.send_whatsapp(
                        to_phone=sender_phone,
                        message=ai_reply_text,
                        distributor_id=distributor_id
                    )
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

