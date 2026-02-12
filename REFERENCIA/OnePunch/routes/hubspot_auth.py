"""
HubSpot OAuth Routes
Handles the OAuth 2.0 flow for connecting HubSpot accounts
"""
import os
import requests
import urllib.parse
from datetime import datetime
from flask import Blueprint, request, redirect, url_for, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.company import Company
from models.user import User

hubspot_auth_bp = Blueprint('hubspot_auth', __name__, url_prefix='/api/auth/hubspot')

@hubspot_auth_bp.route('/authorize', methods=['GET'])
@jwt_required()
def authorize():
    """
    Initiate HubSpot OAuth flow
    Redirects user to HubSpot authorization page
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    client_id = os.getenv('HUBSPOT_CLIENT_ID')
    redirect_uri = os.getenv('HUBSPOT_REDIRECT_URI')
    
    if not client_id or not redirect_uri:
        return jsonify({'error': 'HubSpot configuration missing (Client ID or Redirect URI)'}), 500
    
    # Scopes required for the application (minimal set)
    scopes = [
        'crm.objects.contacts.read',
        'crm.objects.contacts.write',
        'crm.objects.deals.read',
        'crm.objects.deals.write',
        'crm.objects.owners.read'
    ]
    
    # Build state: company_id|next_url
    next_url = request.args.get('next', '/settings')
    state_data = f"{user.company_id}|{next_url}"
    
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(scopes),
        'state': state_data
    }
    
    auth_url = f"https://app.hubspot.com/oauth/authorize?{urllib.parse.urlencode(params)}"
    
    return jsonify({'auth_url': auth_url})


@hubspot_auth_bp.route('/callback', methods=['GET'])
def callback():
    """
    Handle HubSpot OAuth callback
    Exchanges code for access token
    """
    code = request.args.get('code')
    error = request.args.get('error')
    state = request.args.get('state')  # Format: company_id|next_url
    
    # Parse state
    company_id = None
    next_url = '/settings'
    if state and '|' in state:
        parts = state.split('|', 1)
        company_id = parts[0]
        next_url = parts[1] if len(parts) > 1 else '/settings'
    elif state:
        company_id = state
    
    if error:
        return jsonify({'error': f"HubSpot authorization failed: {error}"}), 400
    
    if not code:
        return jsonify({'error': 'No authorization code received'}), 400
        
    client_id = os.getenv('HUBSPOT_CLIENT_ID')
    client_secret = os.getenv('HUBSPOT_CLIENT_SECRET')
    redirect_uri = os.getenv('HUBSPOT_REDIRECT_URI')
    
    if not all([client_id, client_secret, redirect_uri]):
        return jsonify({'error': 'HubSpot configuration missing on server'}), 500
        
    # Exchange code for tokens
    token_url = "https://api.hubapi.com/oauth/v1/token"
    
    payload = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'code': code
    }
    
    try:
        response = requests.post(token_url, data=payload)
        tokens = response.json()
        
        if response.status_code != 200:
            return jsonify({'error': f"Failed to exchange token: {tokens.get('message')}"}), 400
            
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        expires_in = tokens.get('expires_in')
        
        # Save tokens to Company settings
        if company_id:
            company = Company.query.get(company_id)
            if company:
                if company.api_keys is None:
                    company.api_keys = {}
                
                # Update credentials
                creds = company.api_keys.copy() # SQLAlchemy JSON mutation check
                creds['hubspot_access_token'] = access_token
                creds['hubspot_refresh_token'] = refresh_token
                creds['hubspot_token_expires_at'] = datetime.now().timestamp() + expires_in
                
                # Fetch Portal ID for display
                try:
                    info_url = f"https://api.hubapi.com/oauth/v1/access-tokens/{access_token}"
                    info_resp = requests.get(info_url)
                    if info_resp.status_code == 200:
                        creds['hubspot_portal_id'] = info_resp.json().get('hub_id')
                except Exception:
                    pass
                
                company.api_keys = creds
                db.session.commit()
                
                # Dynamic redirect to originating page
                return redirect(f"{next_url}?hubspot=connected")
            
        return jsonify({'error': 'Company not found for state'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
