"""
Company Management Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.company import Company, AgentGender

companies_bp = Blueprint('companies', __name__)


def get_user_company():
    """Helper to get current user's company"""
    user_id = get_jwt_identity()
    print(f"DEBUG: get_user_company() - JWT Identity: {user_id}")
    try:
        uid = int(user_id)
        user = User.query.get(uid)
        print(f"DEBUG: User query result: {user}")
        if not user:
            print(f"DEBUG: User {uid} not found in DB")
            return None, None
        
        print(f"DEBUG: User found: {user.email}, Company: {user.company}")
        if not user.company:
            print(f"DEBUG: User {user.email} has no company association")
            return user, None
            
        return user, user.company
    except Exception as e:
        print(f"DEBUG: Error in get_user_company: {e}")
        return None, None


@companies_bp.route('/', methods=['GET'])
@jwt_required()
def get_company():
    """Get current user's company"""
    user, company = get_user_company()
    
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    return jsonify({'company': company.to_dict()})


@companies_bp.route('/', methods=['PUT'])
@jwt_required()
def update_company():
    """Update company details"""
    print("DEBUG: update_company() called!")
    user, company = get_user_company()
    
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    data = request.get_json()
    print(f"DEBUG: Received data: {data}")
    
    # Update basic info
    if 'name' in data:
        company.name = data['name']
    if 'industry' in data:
        company.industry = data['industry']
    if 'country' in data:
        company.country = data['country']
    if 'city' in data:
        company.city = data['city']
    if 'timezone' in data:
        company.timezone = data['timezone']
    if 'language' in data:
        company.language = data['language']
    if 'email' in data:
        company.email = data['email']
    if 'phone' in data:
        company.phone = data['phone']
    if 'website' in data:
        company.website = data['website']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Company updated',
        'company': company.to_dict()
    })


@companies_bp.route('/agent-settings', methods=['PUT'])
@jwt_required()
def update_agent_settings():
    """Update agent personalization settings"""
    user, company = get_user_company()
    
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    data = request.get_json()
    
    if 'agent_name' in data:
        company.agent_name = data['agent_name']
    
    if 'agent_gender' in data:
        try:
            company.agent_gender = AgentGender(data['agent_gender'])
        except ValueError:
            return jsonify({'error': 'Invalid agent gender'}), 400
    
    if 'personality_prompt' in data:
        company.personality_prompt = data['personality_prompt']
    
    if 'custom_instructions' in data:
        company.custom_instructions = data['custom_instructions']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Agent settings updated',
        'company': company.to_dict()
    })


@companies_bp.route('/llm-config', methods=['GET'])
@jwt_required()
def get_llm_config():
    """Get LLM configuration"""
    user, company = get_user_company()
    
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    return jsonify({
        'llm_provider': company.llm_provider,
        'llm_model': company.llm_model,
        'voice_provider': company.voice_provider,
        'voice_model': company.voice_model,
        'api_keys': {
            # LLM Keys (return actual values for display)
            'openai': company.api_keys.get('openai'),
            'anthropic': company.api_keys.get('anthropic'),
            'google': company.api_keys.get('google'),
            'elevenlabs': company.api_keys.get('elevenlabs'),
            
            # Telephony Provider
            'telephony_provider': company.api_keys.get('telephony_provider'),
            
            # Twilio (All values)
            'twilio_sid': company.api_keys.get('twilio_sid'),
            'twilio_token': company.api_keys.get('twilio_token'),
            'twilio_whatsapp_number': company.api_keys.get('twilio_whatsapp_number'),
            'twilio_voice_number': company.api_keys.get('twilio_voice_number'),
            'twilio_phone': company.api_keys.get('twilio_phone'), # Legacy
            
            # LiveKit (All values)
            'livekit_url': company.api_keys.get('livekit_url'),
            'livekit_api_key': company.api_keys.get('livekit_api_key'),
            'livekit_api_secret': company.api_keys.get('livekit_api_secret'),
            'livekit_caller_id': company.api_keys.get('livekit_caller_id'),
            
            # PayPal (All values)
            'paypal_id': company.api_keys.get('paypal_id'),
            'paypal_secret': company.api_keys.get('paypal_secret'), # Frontend should mask this if needed, or we mask here
            'paypal_mode': company.api_keys.get('paypal_mode'),
            
            # Google Service Account (Full JSON for editing)
            'google_service_account': company.api_keys.get('google_service_account'),
            'google_service_account_configured': bool(company.api_keys.get('google_service_account')),
            
            # Google OAuth (New)
            'google_oauth_credentials': bool(company.api_keys.get('google_oauth_credentials')),
            'google_calendar_id': company.api_keys.get('google_calendar_id'),
            'google_sheet_id': company.api_keys.get('google_sheet_id'),
            
            # HubSpot (New)
            'hubspot_access_token': bool(company.api_keys.get('hubspot_access_token')),
            'hubspot_portal_id': company.api_keys.get('hubspot_portal_id')
        }
    })


@companies_bp.route('/llm-config', methods=['PUT'])
@jwt_required()
def update_llm_config():
    """Update LLM configuration and API keys"""
    user, company = get_user_company()
    
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    data = request.get_json()
    
    if 'llm_provider' in data:
        company.llm_provider = data['llm_provider']
    
    if 'llm_model' in data:
        company.llm_model = data['llm_model']
    
    if 'voice_provider' in data:
        company.voice_provider = data['voice_provider']
    
    if 'voice_model' in data:
        company.voice_model = data['voice_model']
    
    # Update API keys
    # Acceptable keys to update
    ALLOWED_KEYS = [
        'openai', 'anthropic', 'google', 'elevenlabs',
        'telephony_provider',
        'twilio_sid', 'twilio_token', 'twilio_whatsapp_number', 'twilio_voice_number', 'twilio_phone',
        'livekit_url', 'livekit_api_key', 'livekit_api_secret', 'livekit_caller_id',
        'paypal_id', 'paypal_secret', 'paypal_mode',
        'google_service_account'
    ]
    
    if 'api_keys' in data:
        current_keys = company.api_keys or {}
        # Make a copy to avoid modification issues if it's a tracked dict
        new_keys = dict(current_keys) 
        
        for key, value in data['api_keys'].items():
            if key in ALLOWED_KEYS and value:  # Only update allowed keys and if value is provided
                new_keys[key] = value
                
        company.api_keys = new_keys
    
    db.session.commit()
    
    return jsonify({
        'message': 'LLM configuration updated',
        'llm_provider': company.llm_provider,
        'llm_model': company.llm_model
    })


# Available LLM models for reference
LLM_MODELS = {
    'openai': [
        {'id': 'gpt-4', 'name': 'GPT-4'},
        {'id': 'gpt-4-turbo', 'name': 'GPT-4 Turbo'},
        {'id': 'gpt-3.5-turbo', 'name': 'GPT-3.5 Turbo'},
    ],
    'anthropic': [
        {'id': 'claude-3-opus', 'name': 'Claude 3 Opus'},
        {'id': 'claude-3-sonnet', 'name': 'Claude 3 Sonnet'},
        {'id': 'claude-3-haiku', 'name': 'Claude 3 Haiku'},
    ],
    'google': [
        {'id': 'gemini-pro', 'name': 'Gemini Pro'},
        {'id': 'gemini-1.5-pro', 'name': 'Gemini 1.5 Pro'},
    ]
}

VOICE_MODELS = {
    'elevenlabs': [
        {'id': 'eleven_multilingual_v2', 'name': 'Multilingual V2'},
        {'id': 'eleven_turbo_v2', 'name': 'Turbo V2'},
    ],
    'openai': [
        {'id': 'tts-1', 'name': 'TTS-1'},
        {'id': 'tts-1-hd', 'name': 'TTS-1 HD'},
    ]
}


@companies_bp.route('/available-models', methods=['GET'])
@jwt_required()
def get_available_models():
    """Get list of available LLM and voice models"""
    return jsonify({
        'llm_models': LLM_MODELS,
        'voice_models': VOICE_MODELS
    })
