"""
Google OAuth Routes - Handles Google Sign-In for Calendar & Gmail integration.
Migration Path: OAuth tokens will be stored in client-side encrypted vaults.
"""
import os
import json
import logging
from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.distributor import Distributor

logger = logging.getLogger(__name__)

google_auth_bp = Blueprint('google_auth', __name__)

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/userinfo.email',
]


@google_auth_bp.route('/login', methods=['GET'])
@jwt_required()
def google_login():
    """Generate Google OAuth authorization URL.
    Frontend calls this, then redirects the browser to the returned URL.
    """
    db.session.rollback()

    try:
        from google_auth_oauthlib.flow import Flow

        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5000/api/auth/google/callback')

        if not client_id or not client_secret:
            return jsonify({'error': 'Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.'}), 503

        # Build OAuth flow from client config
        client_config = {
            'web': {
                'client_id': client_id,
                'client_secret': client_secret,
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'redirect_uris': [redirect_uri],
            }
        }

        flow = Flow.from_client_config(client_config, scopes=SCOPES)
        flow.redirect_uri = redirect_uri

        # Include user_id in state so callback knows who to associate tokens with
        user_id = get_jwt_identity()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=str(user_id),
        )

        return jsonify({
            'data': {
                'authorization_url': authorization_url,
            }
        }), 200

    except ImportError:
        return jsonify({'error': 'google-auth-oauthlib not installed. Run: pip3 install google-auth-oauthlib'}), 503
    except Exception as e:
        logger.error(f"Google login error: {e}")
        return jsonify({'error': str(e)}), 500


@google_auth_bp.route('/callback', methods=['GET'])
def google_callback():
    """Handle Google OAuth callback.
    Exchanges the authorization code for tokens and stores them
    in the distributor's google_credentials field.
    Then redirects user back to the frontend channels page.
    """
    db.session.rollback()

    try:
        from google_auth_oauthlib.flow import Flow

        code = request.args.get('code')
        state = request.args.get('state')  # user_id
        error = request.args.get('error')

        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')

        if error:
            logger.error(f"Google OAuth error: {error}")
            return redirect(f"{frontend_url}/channels?google_error={error}")

        if not code or not state:
            return redirect(f"{frontend_url}/channels?google_error=missing_params")

        # Rebuild flow
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5000/api/auth/google/callback')

        client_config = {
            'web': {
                'client_id': client_id,
                'client_secret': client_secret,
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'redirect_uris': [redirect_uri],
            }
        }

        flow = Flow.from_client_config(client_config, scopes=SCOPES)
        flow.redirect_uri = redirect_uri

        # Exchange code for tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Save to distributor
        user_id = int(state)
        user = User.query.get(user_id)
        if not user or not user.distributor_id:
            return redirect(f"{frontend_url}/channels?google_error=user_not_found")

        distributor = Distributor.query.get(user.distributor_id)
        if not distributor:
            return redirect(f"{frontend_url}/channels?google_error=distributor_not_found")

        # Store credentials as JSON
        creds_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': list(credentials.scopes) if credentials.scopes else SCOPES,
        }

        distributor.google_credentials = creds_data
        db.session.commit()

        logger.info(f"Google credentials saved for distributor {distributor.id}")
        return redirect(f"{frontend_url}/channels?google_success=true")

    except Exception as e:
        logger.error(f"Google callback error: {e}")
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        return redirect(f"{frontend_url}/channels?google_error={str(e)}")
