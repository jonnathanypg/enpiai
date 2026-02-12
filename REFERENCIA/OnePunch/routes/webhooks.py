"""
Webhook Routes for External Services
Handles incoming webhooks from Twilio, etc.
"""
from flask import Blueprint, request, jsonify
from extensions import db
from models.channel import Channel, ChannelType, ChannelStatus
from models.conversation import Conversation, Message, ConversationType, MessageChannel, MessageRole

# Optional Twilio imports
try:
    from twilio.twiml.messaging_response import MessagingResponse
    from twilio.twiml.voice_response import VoiceResponse
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    MessagingResponse = None
    VoiceResponse = None

import requests
import json

def send_meta_message(token, phone_id, to_phone, text):
    """Send WhatsApp message via Meta Graph API"""
    url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": text}
    }
    try:
        requests.post(url, headers=headers, json=data)
    except Exception as e:
        print(f"Error sending Meta message: {e}")

webhooks_bp = Blueprint('webhooks', __name__)


@webhooks_bp.route('/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages from Twilio"""
    # Get message details
    from_number = request.values.get('From', '')
    to_number = request.values.get('To', '')
    body = request.values.get('Body', '')
    message_sid = request.values.get('MessageSid', '')
    
    # Find the channel by phone number
    channel = Channel.query.filter(
        Channel.type == ChannelType.WHATSAPP,
        Channel.phone_number.like(f'%{to_number.replace("whatsapp:", "")}%')
    ).first()
    
    if not channel:
        # Default response if no channel found
        resp = MessagingResponse()
        resp.message("This number is not configured. Please contact support.")
        return str(resp)
    
    # Update channel activity
    channel.last_activity = db.func.now()
    
    # Find or create conversation
    customer_phone = from_number.replace('whatsapp:', '')
    conversation = Conversation.query.filter_by(
        company_id=channel.company_id,
        channel=MessageChannel.WHATSAPP,
        contact_phone=customer_phone
    ).first()
    
    if not conversation:
        conversation = Conversation(
            company_id=channel.company_id,
            type=ConversationType.CUSTOMER,
            channel=MessageChannel.WHATSAPP,
            contact_phone=customer_phone
        )
        db.session.add(conversation)
        db.session.flush()
    
    # Save incoming message
    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=body,
        channel=MessageChannel.WHATSAPP
    )
    db.session.add(user_message)
    conversation.last_message_at = db.func.now()
    
    db.session.commit()
    
    # Process with AgentService
    try:
        from services.agent_service import AgentService
        agent_service = AgentService(channel.company)
        
        # Determine specific agent if assigned to channel, or default
        agent = None # AgentService will pick default or based on context
        
        # Generate AI response
        response_data = agent_service.process_message(
            conversation=conversation,
            user_message=body,
            agent=agent,
            channel='whatsapp'
        )
        
        assistant_response = response_data.get('content')
        
        # Handle tool-only responses (no content)
        if not assistant_response and response_data.get('tool_calls'):
            # If agent executed tools but gave no text, we might want to stay silent 
            # or give a generic confirmation. For WhatsApp, better to be silent 
            # if it was just an internal action, or send the tool result if relevant.
            # For now, let's skip sending a text reply if it's purely internal actions
            # unless the agent thinks it needs to say something.
            pass 
            
        if assistant_response:
            # Save assistant response to DB
            assistant_message = Message(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=assistant_response,
                channel=MessageChannel.WHATSAPP,
                tool_calls=response_data.get('tool_calls', [])
            )
            db.session.add(assistant_message)
            db.session.commit()
            
            # Send response via Twilio TwiML
            resp = MessagingResponse()
            resp.message(assistant_response)
            return str(resp)
            
    except Exception as e:
        print(f"Error processing WhatsApp agent response: {e}")
        # Fallback to silence or error log, don't crash webhook
        return str(MessagingResponse())

    return str(MessagingResponse())


@webhooks_bp.route('/voice', methods=['POST'])
def voice_webhook():
    """Handle incoming voice calls from Twilio"""
    from_number = request.values.get('From', '')
    to_number = request.values.get('To', '')
    call_sid = request.values.get('CallSid', '')
    
    # Find the channel
    channel = Channel.query.filter(
        Channel.type == ChannelType.VOICE,
        Channel.phone_number.like(f'%{to_number}%')
    ).first()
    
    resp = VoiceResponse()
    
    if not channel:
        resp.say("This number is not configured. Goodbye.")
        resp.hangup()
        return str(resp)
    
    # Update channel activity
    channel.last_activity = db.func.now()
    
    # Create conversation for the call
    conversation = Conversation(
        company_id=channel.company_id,
        type=ConversationType.CUSTOMER,
        channel=MessageChannel.VOICE,
        contact_phone=from_number,
        conv_metadata={'call_sid': call_sid}
    )
    db.session.add(conversation)
    db.session.commit()
    
    # Get company agent name
    agent_name = channel.company.agent_name if channel.company else "the assistant"
    
    # Voice response with gather for input
    resp.say(f"Hello! You've reached {agent_name}. How can I help you today?")
    
    # Gather speech input
    gather = resp.gather(
        input='speech',
        action='/webhooks/voice/process',
        timeout=5,
        speech_timeout='auto'
    )
    gather.say("Please tell me how I can assist you.")
    
    # If no input, prompt again
    resp.say("I didn't catch that. Please try again.")
    resp.redirect('/webhooks/voice')
    
    return str(resp)


@webhooks_bp.route('/voice/process', methods=['POST'])
def voice_process():
    """Process voice input with AgentService"""
    speech_result = request.values.get('SpeechResult', '')
    call_sid = request.values.get('CallSid', '')
    from_number = request.values.get('From', '')
    to_number = request.values.get('To', '')
    
    resp = VoiceResponse()
    
    if not speech_result:
        resp.say("I'm sorry, I couldn't understand. Let me transfer you to a team member.")
        resp.say("Thank you for calling. Goodbye!")
        resp.hangup()
        return str(resp)
    
    # Find the channel for this call
    channel = Channel.query.filter(
        Channel.type == ChannelType.VOICE,
        Channel.phone_number.like(f'%{to_number}%')
    ).first()
    
    if not channel:
        resp.say("I'm sorry, this line is not configured. Goodbye.")
        resp.hangup()
        return str(resp)
    
    try:
        # Find or create conversation for this call
        conversation = Conversation.query.filter_by(
            company_id=channel.company_id,
            channel=MessageChannel.VOICE,
            conv_metadata={'call_sid': call_sid}
        ).first()
        
        if not conversation:
            conversation = Conversation(
                company_id=channel.company_id,
                type=ConversationType.CUSTOMER,
                channel=MessageChannel.VOICE,
                contact_phone=from_number,
                conv_metadata={'call_sid': call_sid}
            )
            db.session.add(conversation)
            db.session.flush()
        
        # Save user's speech as message
        user_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=speech_result,
            channel=MessageChannel.VOICE
        )
        db.session.add(user_message)
        conversation.last_message_at = db.func.now()
        db.session.commit()
        
        # Process with AgentService
        from services.agent_service import AgentService
        agent_service = AgentService(channel.company)
        
        response_data = agent_service.process_message(
            conversation=conversation,
            user_message=speech_result,
            agent=None,
            channel='voice'
        )
        
        assistant_response = response_data.get('content')
        
        if not assistant_response:
            assistant_response = "I'm processing your request. Is there anything else I can help you with?"
        
        # Save assistant response
        assistant_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=assistant_response,
            channel=MessageChannel.VOICE,
            tool_calls=response_data.get('tool_calls', [])
        )
        db.session.add(assistant_message)
        db.session.commit()
        
        # Say the response
        resp.say(assistant_response)
        
        # Gather more input
        gather = resp.gather(
            input='speech',
            action='/webhooks/voice/process',
            timeout=5,
            speech_timeout='auto'
        )
        gather.say("Is there anything else I can help you with?")
        
        # If no input, end call
        resp.say("Thank you for calling. Goodbye!")
        resp.hangup()
        
    except Exception as e:
        print(f"Error processing voice: {e}")
        resp.say("I apologize, but I'm having trouble processing your request. Let me transfer you to a team member.")
        resp.say("Thank you for calling. Goodbye!")
        resp.hangup()
    
    return str(resp)


@webhooks_bp.route('/sms', methods=['POST'])
def sms_webhook():
    """Handle incoming SMS from Twilio"""
    from_number = request.values.get('From', '')
    to_number = request.values.get('To', '')
    body = request.values.get('Body', '')
    
    # Find the channel
    channel = Channel.query.filter(
        Channel.type == ChannelType.SMS,
        Channel.phone_number.like(f'%{to_number}%')
    ).first()
    
    if not channel:
        resp = MessagingResponse()
        resp.message("This number is not configured.")
        return str(resp)
    
    # Update channel activity
    channel.last_activity = db.func.now()
    
    # Find or create conversation
    conversation = Conversation.query.filter_by(
        company_id=channel.company_id,
        channel=MessageChannel.SMS,
        contact_phone=from_number
    ).first()
    
    if not conversation:
        conversation = Conversation(
            company_id=channel.company_id,
            type=ConversationType.CUSTOMER,
            channel=MessageChannel.SMS,
            contact_phone=from_number
        )
        db.session.add(conversation)
        db.session.flush()
    
    # Save incoming message
    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=body,
        channel=MessageChannel.SMS
    )
    db.session.add(user_message)
    conversation.last_message_at = db.func.now()
    db.session.commit()
    
    # Process with AgentService
    try:
        from services.agent_service import AgentService
        agent_service = AgentService(channel.company)
        
        # Generate AI response
        response_data = agent_service.process_message(
            conversation=conversation,
            user_message=body,
            agent=None,
            channel='sms'
        )
        
        assistant_response = response_data.get('content')
        
        # Handle tool-only responses (no content)
        if not assistant_response and response_data.get('tool_calls'):
            # If agent executed tools but gave no text, give a generic confirmation
            tool_names = [t.get('tool', 'unknown') for t in response_data['tool_calls']]
            assistant_response = f"I'm processing your request: {', '.join(tool_names)}. I'll follow up shortly."
            
        if assistant_response:
            # Save assistant response to DB
            assistant_message = Message(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=assistant_response,
                channel=MessageChannel.SMS,
                tool_calls=response_data.get('tool_calls', [])
            )
            db.session.add(assistant_message)
            db.session.commit()
            
            # Send response via Twilio TwiML
            resp = MessagingResponse()
            resp.message(assistant_response)
            return str(resp)
            
    except Exception as e:
        print(f"Error processing SMS agent response: {e}")
        # Fallback to generic response
        resp = MessagingResponse()
        resp.message("Thank you for your message. We'll get back to you soon.")
        return str(resp)

    return str(MessagingResponse())


@webhooks_bp.route('/status', methods=['POST'])
def status_webhook():
    """Handle status callbacks from Twilio"""
    message_sid = request.values.get('MessageSid', '')
    message_status = request.values.get('MessageStatus', '')
    
    # Log status update
    # TODO: Update message status in database
    
    return jsonify({'status': 'received'})


@webhooks_bp.route('/meta', methods=['GET', 'POST'])
def meta_webhook():
    """Handle incoming WhatsApp messages from Meta (Cloud API)"""
    
    # 1. Verification Request (GET)
    if request.method == 'GET':
        mode = request.values.get('hub.mode')
        token = request.values.get('hub.verify_token')
        challenge = request.values.get('hub.challenge')
        
        if mode == 'subscribe' and token:
            # Find any channel with this verify token
            # Note: In production with many channels, this needs optimized query
            channels = Channel.query.filter_by(type=ChannelType.WHATSAPP).all()
            for channel in channels:
                creds = channel.credentials or {}
                if creds.get('verify_token') == token:
                    return challenge, 200
            
            return 'Forbidden', 403
        return 'BadRequest', 400

    # 2. Event Notification (POST)
    data = request.get_json()
    
    try:
        entry = data.get('entry', [])[0]
        changes = entry.get('changes', [])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])
        
        if not messages:
            return jsonify({'status': 'ok'}), 200 # Likely a status update
            
        message = messages[0]
        metadata = value.get('metadata', {})
        phone_number_id = metadata.get('phone_number_id')
        
        # Find channel by phone_number_id
        # We iterate to match credentials JSON field
        channels = Channel.query.filter_by(type=ChannelType.WHATSAPP).all()
        channel = None
        for c in channels:
            creds = c.credentials or {}
            if creds.get('phone_number_id') == phone_number_id:
                channel = c
                break
        
        if not channel:
            print(f"Meta Webhook: No channel found for ID {phone_number_id}")
            return jsonify({'status': 'error', 'message': 'Channel not found'}), 404
            
        # Update activity
        channel.last_activity = db.func.now()
        
        # Extract Message Details
        from_number = message.get('from') # User's WhatsApp number
        body = ''
        if message.get('type') == 'text':
            body = message['text']['body']
        else:
            body = f"[{message.get('type')} message]"
            
        # Find/Create Conversation
        conversation = Conversation.query.filter_by(
            company_id=channel.company_id,
            channel=MessageChannel.WHATSAPP,
            contact_phone=from_number
        ).first()
        
        if not conversation:
            conversation = Conversation(
                company_id=channel.company_id,
                type=ConversationType.CUSTOMER,
                channel=MessageChannel.WHATSAPP,
                contact_phone=from_number
            )
            db.session.add(conversation)
            db.session.flush()
            
        # Save User Message
        user_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=body,
            channel=MessageChannel.WHATSAPP
        )
        db.session.add(user_message)
        conversation.last_message_at = db.func.now()
        db.session.commit()
        
        # Process with Agent
        try:
            from services.agent_service import AgentService
            agent_service = AgentService(channel.company)
            
            response_data = agent_service.process_message(
                conversation=conversation,
                user_message=body,
                agent=None,
                channel='email'
            )
            
            assistant_response = response_data.get('content')
            
            if assistant_response:
                # Save Assistant Message
                assistant_message = Message(
                    conversation_id=conversation.id,
                    role=MessageRole.ASSISTANT,
                    content=assistant_response,
                    channel=MessageChannel.WHATSAPP,
                    tool_calls=response_data.get('tool_calls', [])
                )
                db.session.add(assistant_message)
                db.session.commit()
                
                # Send back via Meta Graph API
                creds = channel.credentials or {}
                token = creds.get('access_token')
                
                if token and phone_number_id:
                    send_meta_message(token, phone_number_id, from_number, assistant_response)
                else:
                    print("Meta Webhook: Missing token for replay")
                    
        except Exception as e:
            print(f"Meta Webhook Agent Error: {e}")
            
    except Exception as e:
        print(f"Meta Webhook Parse Error: {e}")
        return jsonify({'status': 'error'}), 500
        
    return jsonify({'status': 'received'}), 200


@webhooks_bp.route('/telegram/<int:channel_id>', methods=['POST'])
def telegram_webhook(channel_id):
    """Handle incoming Telegram messages"""
    channel = Channel.query.get(channel_id)
    if not channel or channel.type != ChannelType.TELEGRAM:
        return jsonify({'error': 'Invalid channel'}), 404
        
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'status': 'ok'}), 200 # Ignore non-message updates
        
    msg = data['message']
    chat_id = str(msg['chat']['id'])
    user_name = msg['from'].get('first_name', 'Unknown')
    text = msg.get('text', '')
    
    if not text:
        return jsonify({'status': 'ok'}), 200 # Ignore images for now
        
    # Update Channel Activity
    channel.last_activity = db.func.now()
    
    # Conversation
    # Store Chat ID in contact_phone field for consistency
    print(f"[TELEGRAM DEBUG] Looking for conversation: company_id={channel.company_id}, channel=TELEGRAM, contact_phone={chat_id}")
    conversation = Conversation.query.filter_by(
        company_id=channel.company_id,
        channel=MessageChannel.TELEGRAM,
        contact_phone=str(chat_id) 
    ).first()
    print(f"[TELEGRAM DEBUG] Found conversation: {conversation.id if conversation else 'None'}")
    
    if not conversation:
        conversation = Conversation(
            company_id=channel.company_id,
            type=ConversationType.CUSTOMER,
            channel=MessageChannel.TELEGRAM,
            contact_phone=str(chat_id),
            contact_name=user_name
        )
        db.session.add(conversation)
        db.session.flush()
        
    # User Message
    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=text,
        channel=MessageChannel.TELEGRAM
    )
    db.session.add(user_message)
    conversation.last_message_at = db.func.now()
    db.session.commit()
    
    # Agent Processing
    try:
        from services.agent_service import AgentService
        agent_service = AgentService(channel.company)
        
        response_data = agent_service.process_message(
             conversation=conversation,
             user_message=text,
             channel='telegram'
        )
        
        assistant_response = response_data.get('content')
        
        if assistant_response:
             # Save Assistant Message
             asst_msg = Message(
                 conversation_id=conversation.id,
                 role=MessageRole.ASSISTANT,
                 content=assistant_response,
                 channel=MessageChannel.TELEGRAM,
                 tool_calls=response_data.get('tool_calls', [])
             )
             db.session.add(asst_msg)
             db.session.commit()
             
             # Send Reply via Telegram API
             token = channel.credentials.get('telegram_token')
             requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={
                 'chat_id': chat_id,
                 'text': assistant_response
             })
             
    except Exception as e:
        print(f"Telegram Agent Error: {e}")
        
    return jsonify({'status': 'ok'}), 200


@webhooks_bp.route('/webchat/message', methods=['POST'])
def webchat_webhook():
    """
    Webhook for WebChat messages
    """
    # Force clean session start
    db.session.remove()
    
    data = request.get_json()
    widget_id = data.get('widget_id')
    text = data.get('message')
    user_identifier = data.get('user_id', 'guest')
    
    if not widget_id or not text:
        return jsonify({'error': 'Missing widget_id or message'}), 400
        
    # Find Channel by widget_id
    channels = Channel.query.filter_by(type=ChannelType.WEBCHAT).all()
    channel = None
    for c in channels:
        credentials = c.credentials if isinstance(c.credentials, dict) else {}
        if credentials.get('widget_id') == widget_id:
            channel = c
            break
            
    if not channel:
        return jsonify({'error': 'Invalid widget_id'}), 404
        
    # Find or Create Conversation
    conversation = Conversation.query.filter_by(
        company_id=channel.company_id,
        channel=MessageChannel.WEBCHAT.value,
        contact_phone=str(user_identifier),
        is_active=True
    ).first()
    
    if not conversation:
        conversation = Conversation(
            company_id=channel.company_id,
            channel=MessageChannel.WEBCHAT.value,
            contact_phone=str(user_identifier),
            is_active=True,
            type=ConversationType.CUSTOMER
        )
        db.session.add(conversation)
        db.session.commit()
        
    # Set Context for Tools
    from flask import g
    g.current_conversation = conversation
    if channel and channel.company:
        g.current_company = channel.company
    
    # Save User Message
    user_msg = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=text,
        channel=MessageChannel.WEBCHAT
    )
    db.session.add(user_msg)
    conversation.last_message_at = db.func.now()
    db.session.commit()
    
    # Process with Agent
    try:
        from services.agent_service import AgentService
        agent_service = AgentService(channel.company)
        
        response_data = agent_service.process_message(
            conversation=conversation,
            user_message=text,
            channel='webchat',
            thread_id=user_identifier # Use session ID as thread_id for exact context matching
        )
        
        assistant_text = response_data.get('content')
        if assistant_text:
             # Pre-fetch ID to avoid detached instance error during retry
             safe_conversation_id = conversation.id
             
             asst_msg = Message(
                 conversation_id=safe_conversation_id,
                 role=MessageRole.ASSISTANT,
                 content=assistant_text,
                 channel=MessageChannel.WEBCHAT,
                 tool_calls=response_data.get('tool_calls', [])
             )
             db.session.add(asst_msg)
             try:
                 db.session.commit()
             except Exception as db_err:
                 # Retry logic for "MySQL server has gone away"
                 print(f"WebChat DB Error (First Attempt): {db_err}")
                 db.session.rollback()
                 db.session.remove() # Force fresh connection
                 
                 # Re-attach/Re-create object for new session
                 asst_msg = Message(
                     conversation_id=safe_conversation_id, # Use stored ID
                     role=MessageRole.ASSISTANT,
                     content=assistant_text,
                     channel=MessageChannel.WEBCHAT,
                     tool_calls=response_data.get('tool_calls', [])
                 )
                 db.session.add(asst_msg)
                 db.session.commit()
             
             return jsonify({'response': assistant_text})
             
    except Exception as e:
        db.session.rollback()  # Limpiar transacción fallida
        print(f"WebChat Error: {e}")
        return jsonify({'error': 'Agent processing failed'}), 500
        
    return jsonify({'status': 'ok'}), 200
