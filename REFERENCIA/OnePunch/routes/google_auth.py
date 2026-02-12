from flask import Blueprint, redirect, url_for, session, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.google_service import GoogleService
from models.user import User
from extensions import db
import os

google_auth_bp = Blueprint('google_auth', __name__, url_prefix='/api/auth/google')

@google_auth_bp.route('/login')
@jwt_required()
def login():
    """Start Google OAuth flow"""
    # Allow insecure transport for development
    if current_app.debug or current_app.config.get('FLASK_ENV') == 'development':
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # 1. Get current user
    try:
        user_id = int(get_jwt_identity())
    except Exception as e:
        print(f"DEBUG: Google Auth Login - Error getting identity: {e}")
        return jsonify({'error': 'Invalid user identity'}), 401
    
    # 2. Configure redirect uri
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
    
    # 3. Create flow
    flow = GoogleService.create_flow(redirect_uri=redirect_uri)
    
    # 4. Generate authorization url
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent' # Force consent to get refresh_token
    )
    
    # 5. Store state and next_url in session
    session['state'] = state
    session['user_id'] = user_id
    
    # Check for 'next' parameter for dynamic redirect
    next_url = request.args.get('next')
    if next_url:
        session['next_url'] = next_url
    
    return jsonify({'url': authorization_url})

@google_auth_bp.route('/callback')
def callback():
    """Handle Google OAuth callback"""
    # Allow insecure transport for development
    if current_app.debug or current_app.config.get('FLASK_ENV') == 'development':
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        
    # 1. Verify state
    # ... (state verification logic if implemented strict) ...
    
    # 2. Get redirect URI again
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
    
    try:
        # 3. Create flow and fetch token
        flow = GoogleService.create_flow(redirect_uri=redirect_uri)
        flow.fetch_token(authorization_response=request.url)
        
        credentials = flow.credentials
        
        # 4. Store credentials in DB
        if 'user_id' not in session:
           return jsonify({'error': 'Session lost during OAuth flow. user_id missing'}), 400
           
        user_id = session['user_id']
        user = User.query.get(user_id)
        
        if not user:
             return jsonify({'error': 'User not found'}), 404
             
        # Convert credentials to json
        creds_json = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        user.google_credentials = creds_json
        
        # 5. Auto-Promote to Company Level (so Agent can use it immediately)
        if user.company:
            company = user.company
            if company.api_keys is None:
                company.api_keys = {}
            
            # Create copy to ensure mutation is tracked
            keys = company.api_keys.copy()
            keys['google_oauth_credentials'] = creds_json
            keys['google_auth_mode'] = 'oauth'
            
            company.api_keys = keys
        
        db.session.commit()
        
        # 6. Dynamic Redirect
        frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5001')
        next_url = session.get('next_url')
        
        if next_url:
             # If next_url is relative (starts with /), append to frontend_url
             if next_url.startswith('/'):
                 return redirect(f"{frontend_url}{next_url}?google_connected=true")
             else:
                 return redirect(f"{next_url}?google_connected=true")
        
        # Default fallback
        return redirect(f"{frontend_url}/channels?google_connected=true")
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@google_auth_bp.route('/status')
@jwt_required()
def status():
    """Check if user has Google connected"""
    # Allow insecure transport for development
    if current_app.debug or current_app.config.get('FLASK_ENV') == 'development':
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
    except Exception as e:
        print(f"DEBUG: Google Auth Status - Error: {e}")
        return jsonify({'error': 'Invalid user identity'}), 401
    
    connected = False
    calendar_status = "Disconnected"
    
    if user and user.google_credentials:
        # Try initializing service to check validity
        try:
            print(f"DEBUG: Checking Google Auth Status for User {user.email}")
            service = GoogleService(user)
            
            if service.creds:
                 print(f"DEBUG: Creds found. Valid: {service.creds.valid}, Expired: {service.creds.expired}, Has Refresh Token: {bool(service.creds.refresh_token)}")
                 if service.creds.expired and service.creds.refresh_token:
                      try:
                          from google.auth.transport.requests import Request
                          service.creds.refresh(Request())
                          print("DEBUG: Token refreshed successfully")
                      except Exception as re:
                          print(f"DEBUG: Token refresh failed: {re}")
            
            if service.is_authenticated():
                connected = True
                calendar_status = "Connected"
            else:
                print("DEBUG: is_authenticated() returned False")
                
        except Exception as e:
            print(f"DEBUG: Google Auth Status - Exception: {e}")
            import traceback
            traceback.print_exc()
            
    return jsonify({
        'connected': connected,
        'services': {
            'calendar': calendar_status,
            'sheets': calendar_status # Using same scope for now
        }
    })

@google_auth_bp.route('/disconnect', methods=['POST'])
@jwt_required()
def disconnect():
    """Remove Google credentials"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
    except Exception as e:
        print(f"DEBUG: Google Auth Disconnect - Error: {e}")
        return jsonify({'error': 'Invalid user identity'}), 401
    
    if user:
        user.google_credentials = None
        db.session.commit()
        return jsonify({'status': 'disconnected'})
    
    return jsonify({'error': 'User not found'}), 404

@google_auth_bp.route('/calendars', methods=['GET'])
@jwt_required()
def list_calendars():
    """List available calendars"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or not user.google_credentials:
            return jsonify({'error': 'Google not connected'}), 400
            
        service = GoogleService(user)
        calendars = service.list_calendars()
        
        # Format for frontend
        options = [{'id': c['id'], 'name': c.get('summary', 'Unknown')} for c in calendars]
        return jsonify({'calendars': options})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@google_auth_bp.route('/sheets', methods=['GET'])
@jwt_required()
def list_sheets():
    """List available sheets"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or not user.google_credentials:
            return jsonify({'error': 'Google not connected'}), 400
            
        service = GoogleService(user)
        # Allow insecure transport for list_sheets too if needed implicitly by google lib? usually just for OAuth flow
        if current_app.debug or current_app.config.get('FLASK_ENV') == 'development':
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

        sheets = service.list_sheets()
        
        # Format for frontend
        options = [{'id': s['id'], 'name': s.get('name', 'Unknown')} for s in sheets]
        return jsonify({'sheets': options})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@google_auth_bp.route('/config', methods=['POST'])
@jwt_required()
def save_config():
    """
    Save selected Google resources and promote user credentials to Company
    This allows agents (backend) to use this user's connection.
    """
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or not user.google_credentials:
            return jsonify({'error': 'Google not connected'}), 400
            
        data = request.json
        calendar_id = data.get('calendar_id')
        sheet_id = data.get('sheet_id')
        
        if not user.company:
             return jsonify({'error': 'User has no company'}), 400
             
        # Promote credentials to Company level
        company = user.company
        if company.api_keys is None:
            company.api_keys = {}
            
        # Create a copy to modify
        keys = company.api_keys.copy()
        keys['google_oauth_credentials'] = user.google_credentials
        
        if calendar_id:
            keys['google_calendar_id'] = calendar_id
            
        if sheet_id:
            keys['google_sheet_id'] = sheet_id
            
        # Signal that we are using OAuth now, not Service Account
        keys['google_auth_mode'] = 'oauth'
        
        company.api_keys = keys
        db.session.commit()
        
        return jsonify({'status': 'saved', 'message': 'Google integration configured for Company'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
