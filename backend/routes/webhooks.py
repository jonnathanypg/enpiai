"""
Webhook Routes - Receive messages from WhatsApp (api-whatsapp) and Telegram.
These are the entry points for external messaging services.

Architecture: "Fire & Forget" pattern — webhooks acknowledge immediately (200 OK)
and dispatch AI processing to Celery workers for non-blocking throughput.

Migration Path: Webhooks will be replaced by P2P message brokers.
"""
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from extensions import db
from models.conversation import Conversation, Message, ConversationChannel, ConversationStatus, MessageRole
from models.lead import Lead, LeadSource
from models.channel import Channel, ChannelType

logger = logging.getLogger(__name__)

# Import email service for notifications
try:
    from services.email_service import email_service
except ImportError:
    email_service = None

webhooks_bp = Blueprint('webhooks', __name__)


# ---------------------------------------------------------------------------
# Celery Tasks for async processing
# ---------------------------------------------------------------------------

def _process_message_async(distributor_id, conversation_id, message_text, channel, sender_phone=None, chat_id=None):
    """
    Dispatch AI processing to Celery. Falls back to sync if Celery is unavailable.
    """
    try:
        from tasks import process_webhook_message
        process_webhook_message.delay(
            distributor_id=distributor_id,
            conversation_id=conversation_id,
            message_text=message_text,
            channel=channel,
            sender_phone=sender_phone,
            chat_id=chat_id
        )
        logger.info(f"Webhook message dispatched to Celery (conv={conversation_id})")
        return True
    except Exception as e:
        logger.warning(f"Celery dispatch failed ({e}), processing synchronously")
        return _process_message_sync(distributor_id, conversation_id, message_text, channel, sender_phone, chat_id)


def _process_message_sync(distributor_id, conversation_id, message_text, channel, sender_phone=None, chat_id=None):
    """
    Synchronous fallback when Celery is unavailable.
    """
    try:
        from models.distributor import Distributor
        from services.agent_orchestrator import get_agent_orchestrator

        distributor = Distributor.query.get(distributor_id)
        conversation = Conversation.query.get(conversation_id)

        if not distributor or not conversation:
            logger.error(f"Sync fallback: Distributor or Conversation not found")
            return False

        orchestrator = get_agent_orchestrator(distributor)
        response_data = orchestrator.process_message(
            conversation=conversation,
            user_message=message_text,
            channel=channel
        )

        ai_reply_text = response_data.get('content')
        if ai_reply_text:
            ai_msg = Message(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=ai_reply_text,
                message_metadata={'agent_name': response_data.get('agent_name')}
            )
            db.session.add(ai_msg)
            conversation.last_message_at = datetime.utcnow()
            db.session.commit()

            # Send reply back to channel
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
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Sync processing error: {e}")
        return False


# ---------------------------------------------------------------------------
# WhatsApp Webhook
# ---------------------------------------------------------------------------

@webhooks_bp.route('/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """
    Receive messages from the api-whatsapp Node.js service.
    Fire & Forget: saves message, dispatches AI to Celery, returns 200 immediately.
    """
    try:
        db.session.rollback()
    except:
        pass

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        distributor_id = data.get('companyId')
        sender_phone = data.get('from', '').strip()
        sender_name = data.get('fromName', '')
        message_text = data.get('message', '')

        if not distributor_id or not sender_phone or not message_text:
            return jsonify({'error': 'companyId, from, and message are required'}), 400

        logger.info(f"WhatsApp message from {sender_phone} for distributor {distributor_id}")

        # 1. Get Distributor
        from models.distributor import Distributor
        distributor = Distributor.query.get(distributor_id)
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        # 2. Find/Create Conversation
        conversation = Conversation.query.filter_by(
            distributor_id=distributor_id,
            channel=ConversationChannel.WHATSAPP,
            participant_id=sender_phone,
            status=ConversationStatus.ACTIVE
        ).first()

        if not conversation:
            conversation = Conversation(
                distributor_id=distributor_id,
                channel=ConversationChannel.WHATSAPP,
                participant_id=sender_phone,
                participant_name=sender_name,
            )
            db.session.add(conversation)
            db.session.flush()

        # 3. Handle Lead Assignment (Agent-Driven)
        # Webhooks no longer auto-create Leads. They map to existing Leads if available.
        # Otherwise, the Conversation stays anonymous until the Agent captures the Lead.
        lead = Lead.query.filter_by(distributor_id=distributor_id, phone=sender_phone).first()
        if lead and not conversation.lead_id:
            conversation.lead_id = lead.id

        # 4. Save User Message (synchronous — fast DB write)
        user_msg = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=message_text,
            message_metadata={
                'messageId': data.get('messageId'),
                'timestamp': data.get('timestamp')
            }
        )
        db.session.add(user_msg)
        conversation.last_message_at = datetime.utcnow()
        db.session.commit()

        # 5. Dispatch AI processing to Celery (Fire & Forget)
        _process_message_async(
            distributor_id=distributor_id,
            conversation_id=conversation.id,
            message_text=message_text,
            channel='whatsapp',
            sender_phone=sender_phone
        )

        # 6. Return immediately — don't block the webhook caller
        return jsonify({
            'status': 'accepted',
            'conversation_id': conversation.id,
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"WhatsApp webhook error: {e}")
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Telegram Webhook
# ---------------------------------------------------------------------------

@webhooks_bp.route('/telegram', methods=['POST'])
def telegram_webhook():
    """
    Receive messages from Telegram bot webhook.
    Fire & Forget: saves message, dispatches AI to Celery, returns 200 immediately.
    """
    try:
        db.session.rollback()
    except:
        pass

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        tg_message = data.get('message', {})
        chat = tg_message.get('chat', {})
        chat_id = str(chat.get('id', ''))
        sender_first = chat.get('first_name', '')
        sender_last = chat.get('last_name', '')
        sender_name = f"{sender_first} {sender_last}".strip()
        message_text = tg_message.get('text', '')

        if not chat_id or not message_text:
            return jsonify({'status': 'ignored'}), 200

        # TODO: Dynamic Distributor Mapping for Telegram
        # For now, resolve from Channel config or default to ID 1
        distributor_id = 1

        from models.distributor import Distributor
        distributor = Distributor.query.get(distributor_id)
        if not distributor:
            return jsonify({'status': 'ignored_no_distributor'}), 200

        # 2. Find/Create Conversation
        conversation = Conversation.query.filter_by(
            distributor_id=distributor_id,
            channel=ConversationChannel.TELEGRAM,
            participant_id=chat_id,
            status=ConversationStatus.ACTIVE
        ).first()

        if not conversation:
            conversation = Conversation(
                distributor_id=distributor_id,
                channel=ConversationChannel.TELEGRAM,
                participant_id=chat_id,
                participant_name=sender_name,
            )
            db.session.add(conversation)
            
            # Map existing Lead if possible, else leave anonymous
            lead = Lead.query.filter_by(
                distributor_id=distributor_id, 
                first_name=sender_first, 
                last_name=sender_last
            ).first()
            if lead:
                conversation.lead_id = lead.id
                
            db.session.flush()

        # 3. Save User Message (synchronous — fast DB write)
        user_msg = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=message_text,
            message_metadata={'telegram_update': data}
        )
        db.session.add(user_msg)
        conversation.last_message_at = datetime.utcnow()
        db.session.commit()

        # 4. Dispatch AI processing to Celery (Fire & Forget)
        _process_message_async(
            distributor_id=distributor_id,
            conversation_id=conversation.id,
            message_text=message_text,
            channel='telegram',
            chat_id=chat_id
        )

        # 5. Return immediately
        return jsonify({'status': 'accepted'}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Telegram webhook error: {e}")
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# dLocal Go Webhook
# ---------------------------------------------------------------------------

@webhooks_bp.route('/dlocal', methods=['POST'])
def dlocal_webhook():
    """
    Receive payment/subscription updates from dLocal Go.
    Updates the distributor's subscription_active status based on `external_id`.
    """
    try:
        db.session.rollback()
    except:
        pass

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        logger.info(f"dLocal Go Webhook Event: {data}")

        # Try to extract external_id (which we map to distributor_id)
        external_id = data.get('external_id')
        status = data.get('status') # Usually "CONFIRMED" or "COMPLETED" or "DECLINED"
        
        # Sometimes the payload is an execution object containing a subscription object
        if not external_id and 'subscription' in data:
            pass # Fallback if needed.

        if external_id:
            try:
                distributor_id = int(external_id)
                from models.distributor import Distributor
                distributor = Distributor.query.get(distributor_id)
                
                if distributor:
                    logger.info(f"dLocal Webhook -> Distributor {distributor_id}. Status: {status}")
                    
                    if status in ['CONFIRMED', 'COMPLETED', 'ACTIVE']:
                        distributor.subscription_active = True
                        # Send subscription activated email
                        if email_service:
                            try:
                                user = None
                                from models.user import User
                                user = User.query.filter_by(distributor_id=distributor_id).first()
                                if user:
                                    email_service.send_subscription_activated(user.email, distributor.name, lang=distributor.language or 'en')
                            except Exception as mail_err:
                                logger.warning(f"Subscription activated email failed: {mail_err}")
                    elif status in ['DECLINED', 'CANCELLED', 'INACTIVE', 'PAST_DUE']:
                        distributor.subscription_active = False
                        # Send subscription deactivated email
                        if email_service:
                            try:
                                from models.user import User
                                user = User.query.filter_by(distributor_id=distributor_id).first()
                                if user:
                                    email_service.send_subscription_deactivated(user.email, distributor.name, reason=status, lang=distributor.language or 'en')
                            except Exception as mail_err:
                                logger.warning(f"Subscription deactivated email failed: {mail_err}")
                        
                    db.session.commit()
                    return jsonify({'status': 'processed'}), 200
                else:
                    logger.warning(f"Distributor not found for external_id: {external_id}")
            except ValueError:
                logger.error(f"Invalid external_id format: {external_id}")
                
        return jsonify({'status': 'ignored'}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"dLocal Go webhook error: {e}")
        return jsonify({'error': str(e)}), 500
