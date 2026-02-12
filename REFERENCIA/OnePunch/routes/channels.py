"""
Channel Management Routes
"""
from datetime import datetime, timedelta
import uuid  # Added for Webchat
import requests # Added for Telegram
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.channel import Channel, ChannelType, ChannelStatus

channels_bp = Blueprint('channels', __name__)


def get_user_company():
    """Helper to get current user's company"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or not user.company:
            print(f"DEBUG: Channels - User/Company missing for ID {user_id}")
            return None
        return user.company
    except Exception as e:
        print(f"DEBUG: Channels - Error: {e}")
        return None


@channels_bp.route('/', methods=['GET'])
@jwt_required()
def list_channels():
    """List all channels for the company"""
    company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    channels = Channel.query.filter_by(company_id=company.id).all()
    # Include credentials so UI can pre-fill forms (secrets should be masked by frontend or here if refined)
    return jsonify({'channels': [c.to_dict(include_credentials=True) for c in channels]})


@channels_bp.route('/<channel_type>', methods=['GET'])
@jwt_required()
def get_channel(channel_type):
    """Get specific channel details"""
    company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    try:
        ctype = ChannelType(channel_type)
    except ValueError:
        return jsonify({'error': 'Invalid channel type'}), 400
    
    channel = Channel.query.filter_by(company_id=company.id, type=ctype).first()
    if not channel:
        return jsonify({'error': 'Channel not found'}), 404
    
    return jsonify({'channel': channel.to_dict(include_credentials=True)})


@channels_bp.route('/connect', methods=['POST'])
@jwt_required()
def connect_channel():
    """Initiate channel connection"""
    company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    data = request.get_json()
    
    try:
        channel_type = ChannelType(data.get('type'))
    except ValueError:
        return jsonify({'error': 'Invalid channel type'}), 400
    
    # Check if channel already exists
    channel = Channel.query.filter_by(
        company_id=company.id,
        type=channel_type
    ).first()
    
    if not channel:
        channel = Channel(
            company_id=company.id,
            type=channel_type,
            name=data.get('name', channel_type.value.title())
        )
        db.session.add(channel)
        db.session.flush() # Generate ID for webhooks
    
    # Handle different channel types
    if channel_type == ChannelType.WHATSAPP:
        return connect_whatsapp(channel, data)
    elif channel_type == ChannelType.EMAIL:
        return connect_email(channel, data)
    elif channel_type == ChannelType.VOICE:
        return connect_voice(channel, data)
    elif channel_type == ChannelType.SMS:
        return connect_sms(channel, data)
    elif channel_type == ChannelType.TELEGRAM:
        return connect_telegram(channel, data)
    elif channel_type == ChannelType.WEBCHAT:
        return connect_webchat(channel, data)
    else:
        return jsonify({'error': 'Channel type not supported'}), 400


def connect_whatsapp(channel, data):
    """Connect WhatsApp channel via Twilio or Meta (Cloud API)"""
    credentials = data.get('credentials', {})
    provider = data.get('provider', 'twilio')  # Default to twilio
    
    if provider == 'meta':
        # WhatsApp Cloud API (Meta)
        if credentials.get('phone_number_id') and credentials.get('access_token'):
            # Save to Channel
            channel.credentials = {
                'provider': 'meta',
                'phone_number_id': credentials['phone_number_id'],
                'waba_id': credentials.get('waba_id'), # WhatsApp Business Account ID
                'access_token': credentials['access_token'],
                'verify_token': credentials.get('verify_token'), # Webhook verify token
                'phone_number': credentials.get('phone_number') # Display number
            }
            channel.phone_number = credentials.get('phone_number')
            channel.update_status(ChannelStatus.CONNECTED, 'Connected via Meta (Cloud API)')
            
            # Sync to Company API Keys (if needed for global access)
            company = channel.company
            if not company.api_keys: company.api_keys = {}
            
            company.api_keys['whatsapp_provider'] = 'meta'
            company.api_keys['meta_phone_id'] = credentials['phone_number_id']
            company.api_keys['meta_waba_id'] = credentials.get('waba_id')
            company.api_keys['meta_token'] = credentials['access_token']
            
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(company, "api_keys")
            
        else:
            return jsonify({'error': 'Phone Number ID and Access Token are required'}), 400

    elif provider == 'twilio':
        # Twilio WhatsApp
        if credentials.get('account_sid'):
            # Merge with existing
            existing = channel.credentials or {}
            new_creds = {
                'provider': 'twilio',
                'account_sid': credentials.get('account_sid'),
                'phone_number': credentials.get('phone_number')
            }
            
            # Handle auth_token
            auth_token = credentials.get('auth_token')
            if auth_token and auth_token != '********':
                new_creds['auth_token'] = auth_token
            elif existing.get('auth_token'):
                new_creds['auth_token'] = existing.get('auth_token')
                
            channel.credentials = new_creds
            channel.phone_number = credentials.get('phone_number')
            channel.update_status(ChannelStatus.CONNECTED, 'Connected via Twilio')

            # Sync to Company API Keys
            company = channel.company
            if not company.api_keys: company.api_keys = {}
            
            company.api_keys['whatsapp_provider'] = 'twilio'
            company.api_keys['twilio_sid'] = new_creds['account_sid']
            if new_creds.get('auth_token'):
                company.api_keys['twilio_token'] = new_creds['auth_token']
            if new_creds.get('phone_number'):
                company.api_keys['twilio_whatsapp_number'] = new_creds['phone_number']
            
            # Fallback telephony provider if not set
            if not company.api_keys.get('telephony_provider'):
                 company.api_keys['telephony_provider'] = 'twilio'
            
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(company, "api_keys")

        else:
            # Sandbox logic (legacy or dev)
            channel.update_status(ChannelStatus.CONNECTING, 'Awaiting connection')
            channel.qr_code = f"whatsapp://send?phone=+14155238886&text=join%20{channel.company_id}-sandbox"
            channel.qr_expires_at = datetime.utcnow() + timedelta(minutes=15)
            
    else:
        return jsonify({'error': 'Unknown provider'}), 400
    
    db.session.commit()
    
    return jsonify({
        'message': f'WhatsApp connection initiated via {provider.title()}',
        'channel': channel.to_dict()
    })


def connect_email(channel, data):
    """Connect Email channel via SendGrid/SMTP"""
    credentials = data.get('credentials', {})
    existing = channel.credentials or {}
    
    # SendGrid
    if credentials.get('api_key') or (existing.get('provider') == 'sendgrid' and existing.get('api_key')):
        # Merge
        new_creds = {
            'provider': 'sendgrid',
            'from_email': credentials.get('from_email')
        }
        
        api_key = credentials.get('api_key')
        if api_key and api_key != '********':
            new_creds['api_key'] = api_key
        elif existing.get('api_key'):
             new_creds['api_key'] = existing.get('api_key')
             
        channel.credentials = new_creds
        channel.email_address = credentials.get('from_email')
        channel.update_status(ChannelStatus.CONNECTED, 'Connected via SendGrid')
        
    elif credentials.get('smtp_host') or (existing.get('provider') == 'smtp' and existing.get('smtp_host')):
        # SMTP/IMAP Credentials
        # Merge
        new_creds = {
            'provider': 'smtp',
            'imap_host': credentials.get('imap_host'),
            'imap_port': credentials.get('imap_port'),
            'imap_encryption': credentials.get('imap_encryption'),
            'smtp_host': credentials.get('smtp_host'),
            'smtp_port': credentials.get('smtp_port'),
            'smtp_encryption': credentials.get('smtp_encryption'),
            'email_user': credentials.get('email_user'),
            'from_email': credentials.get('from_email')
        }
        
        email_pass = credentials.get('email_pass')
        if email_pass and email_pass != '********':
            new_creds['email_pass'] = email_pass
        elif existing.get('email_pass'):
            new_creds['email_pass'] = existing.get('email_pass')
            
        channel.credentials = new_creds
        channel.email_address = credentials.get('from_email')
        channel.update_status(ChannelStatus.CONNECTED, 'Connected via Custom SMTP/IMAP')
    else:
        return jsonify({'error': 'Email credentials required'}), 400
    
    db.session.commit()
    
    return jsonify({
        'message': 'Email channel connected',
        'channel': channel.to_dict(include_credentials=False) # Don't return secrets in response
    })


def connect_voice(channel, data):
    """Connect Voice channel via Twilio or LiveKit"""
    credentials = data.get('credentials', {})
    provider = data.get('provider', 'twilio')  # Default to twilio for backward compatibility
    
    if provider == 'livekit':
        if credentials.get('livekit_url') and credentials.get('livekit_api_key') and credentials.get('livekit_api_secret'):
            # Save to Channel
            channel.credentials = {
                'provider': 'livekit',
                'livekit_url': credentials['livekit_url'],
                'livekit_api_key': credentials['livekit_api_key'],
                'livekit_api_secret': credentials['livekit_api_secret'],
                'livekit_caller_id': credentials.get('livekit_caller_id')
            }
            channel.phone_number = credentials.get('livekit_caller_id', 'LiveKit VoIP')
            channel.update_status(ChannelStatus.CONNECTED, 'Connected via LiveKit')
            
            # Sync to Company API Keys (for LiveKitService)
            company = channel.company
            if not company.api_keys:
                company.api_keys = {}
            
            company.api_keys['livekit_url'] = credentials['livekit_url']
            company.api_keys['livekit_api_key'] = credentials['livekit_api_key']
            company.api_keys['livekit_api_secret'] = credentials['livekit_api_secret']
            if credentials.get('livekit_caller_id'):
                company.api_keys['livekit_caller_id'] = credentials['livekit_caller_id']
            
            # Also set global telephony provider to LiveKit if not set
            if not company.api_keys.get('telephony_provider'):
                 company.api_keys['telephony_provider'] = 'livekit'
            
            # Trigger updates
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(company, "api_keys")
            
        else:
            return jsonify({'error': 'LiveKit URL, API Key, and Secret are required'}), 400

    elif provider == 'twilio':
        if credentials.get('account_sid'):
            # Merge
            existing = channel.credentials or {}
            new_creds = {
                'provider': 'twilio',
                'account_sid': credentials.get('account_sid'),
                'phone_number': credentials.get('phone_number')
            }
            
            auth_token = credentials.get('auth_token')
            if auth_token and auth_token != '********':
                new_creds['auth_token'] = auth_token
            elif existing.get('auth_token'):
                new_creds['auth_token'] = existing.get('auth_token')
                
            channel.credentials = new_creds
            channel.phone_number = credentials.get('phone_number')
            channel.update_status(ChannelStatus.CONNECTED, 'Connected via Twilio')
            
            # Sync to Company API Keys
            company = channel.company
            if not company.api_keys: company.api_keys = {}
                
            company.api_keys['twilio_sid'] = new_creds['account_sid']
            if new_creds.get('auth_token'):
                company.api_keys['twilio_token'] = new_creds['auth_token']
            if new_creds.get('phone_number'):
                company.api_keys['twilio_voice_number'] = new_creds['phone_number']
                
            # Also set global telephony provider to Twilio if not set
            if not company.api_keys.get('telephony_provider'):
                 company.api_keys['telephony_provider'] = 'twilio'
            
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(company, "api_keys")
            
        else:
            return jsonify({'error': 'Twilio credentials required'}), 400
            
    else:
         return jsonify({'error': 'Unknown provider'}), 400
    
    db.session.commit()
    
    return jsonify({
        'message': f'Voice channel connected via {provider.title()}',
        'channel': channel.to_dict()
    })


def connect_sms(channel, data):
    """Connect SMS channel via Twilio"""
    credentials = data.get('credentials', {})
    
    if credentials.get('account_sid'):
        # Merge
        existing = channel.credentials or {}
        new_creds = {
            'account_sid': credentials.get('account_sid'),
            'phone_number': credentials.get('phone_number')
        }
        
        auth_token = credentials.get('auth_token')
        if auth_token and auth_token != '********':
            new_creds['auth_token'] = auth_token
        elif existing.get('auth_token'):
            new_creds['auth_token'] = existing.get('auth_token')

        channel.credentials = new_creds
        channel.phone_number = credentials.get('phone_number')
        channel.update_status(ChannelStatus.CONNECTED, 'Connected via Twilio')
    else:
        return jsonify({'error': 'Twilio credentials required'}), 400
    
    db.session.commit()
    
    return jsonify({
        'message': 'SMS channel connected',
        'channel': channel.to_dict(include_credentials=False)
    })


@channels_bp.route('/<channel_type>/disconnect', methods=['POST'])
@jwt_required()
def disconnect_channel(channel_type):
    """Disconnect a channel"""
    company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    try:
        ctype = ChannelType(channel_type)
    except ValueError:
        return jsonify({'error': 'Invalid channel type'}), 400
    
    channel = Channel.query.filter_by(company_id=company.id, type=ctype).first()
    if not channel:
        return jsonify({'error': 'Channel not found'}), 404
    
    channel.update_status(ChannelStatus.DISCONNECTED, 'Manually disconnected')
    channel.credentials = {}
    db.session.commit()
    
    return jsonify({
        'message': 'Channel disconnected',
        'channel': channel.to_dict()
    })


@channels_bp.route('/<channel_type>/test', methods=['POST'])
@jwt_required()
def test_channel(channel_type):
    """Test channel connection"""
    company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    try:
        ctype = ChannelType(channel_type)
    except ValueError:
        return jsonify({'error': 'Invalid channel type'}), 400
    
    channel = Channel.query.filter_by(company_id=company.id, type=ctype).first()
    if not channel:
        return jsonify({'error': 'Channel not found'}), 404
    
    if channel.status != ChannelStatus.CONNECTED:
        return jsonify({'error': 'Channel is not connected'}), 400
    
    # TODO: Implement actual channel testing
    # For now, return success
    return jsonify({
        'message': 'Test successful',
        'status': 'ok'
    })


@channels_bp.route('/types', methods=['GET'])
@jwt_required()
def get_channel_types():
    """Get available channel types"""
    return jsonify({
        'types': [
            {
                'id': 'whatsapp',
                'name': 'WhatsApp',
                'description': 'Send and receive WhatsApp messages',
                'icon': 'whatsapp',
                'requires': ['Twilio Account']
            },
            {
                'id': 'voice',
                'name': 'Voice Calls',
                'description': 'Handle inbound and outbound voice calls',
                'icon': 'phone',
                'requires': ['Twilio Account', 'Phone Number']
            },
            {
                'id': 'sms',
                'name': 'SMS',
                'description': 'Send and receive SMS messages',
                'icon': 'message-square',
                'requires': ['Twilio Account', 'Phone Number']
            },
            {
                'id': 'email',
                'name': 'Email',
                'description': 'Send and receive emails',
                'icon': 'mail',
                'requires': ['SendGrid API Key or SMTP']
            },
            {
                'id': 'telegram',
                'name': 'Telegram',
                'description': 'Connect a Telegram Bot',
                'icon': 'send',
                'requires': ['Bot Token']
            },
            {
                'id': 'webchat',
                'name': 'Web Chat',
                'description': 'Embed chat widget on your website',
                'icon': 'message-circle',
                'requires': ['Script Installation']
            }
        ]
    })


def connect_telegram(channel, data):
    """Connect Telegram Bot"""
    credentials = data.get('credentials', {})
    token = credentials.get('telegram_token')
    
    # If no new token provided, try to use existing one
    if not token and channel.credentials:
        token = channel.credentials.get('telegram_token')
    
    if not token:
        return jsonify({'error': 'Telegram Bot Token required'}), 400
        
    try:
        # Verify Token
        resp = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if resp.status_code != 200:
             return jsonify({'error': 'Invalid Telegram Token'}), 400
        
        bot_data = resp.json().get('result', {})
        bot_username = bot_data.get('username')
        
        # Set Webhook
        try:
            base_url = current_app.config.get('API_BASE_URL', 'http://localhost:5001')
        except:
             base_url = 'http://localhost:5001'
             
        webhook_url = f"{base_url}/webhooks/telegram/{channel.id}"
        
        # Call SetWebhook
        # Telegram API requires https for webhooks usually
        wh_resp = requests.post(f"https://api.telegram.org/bot{token}/setWebhook", json={'url': webhook_url})
        if wh_resp.status_code != 200:
             print(f"Warning: SetWebhook failed: {wh_resp.text}")
             
        channel.credentials = {
            'provider': 'telegram',
            'telegram_token': token,
            'bot_username': bot_username,
            'webhook_url': webhook_url
        }
        channel.update_status(ChannelStatus.CONNECTED, f"Connected as @{bot_username}")
        
    except Exception as e:
         return jsonify({'error': f"Telegram connection error: {str(e)}"}), 500
    
    db.session.commit()
    return jsonify({
        'message': 'Telegram connected',
        'channel': channel.to_dict(include_credentials=False)
    })


def connect_webchat(channel, data):
    """Connect Web Chat Widget"""
    # Generate unique ID for this widget instance
    if not channel.credentials or 'widget_id' not in channel.credentials:
        widget_id = str(uuid.uuid4())
        channel.credentials = {'widget_id': widget_id}
    
    channel.update_status(ChannelStatus.CONNECTED, 'Widget Ready')
    db.session.commit()
    
    return jsonify({
        'message': 'Web Chat Widget generated',
        'channel': channel.to_dict(include_credentials=True) # UI needs widget_id
    })
