"""
Google OAuth Routes - Handles Google Sign-In for Calendar & Gmail integration.
Migration Path: OAuth tokens will be stored in client-side encrypted vaults.
"""
import hashlib
import base64
import os
import secrets
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


def _build_client_config():
    """Build Google OAuth client configuration from environment variables."""
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5000/api/auth/google/callback')
    return {
        'web': {
            'client_id': client_id,
            'client_secret': client_secret,
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'redirect_uris': [redirect_uri],
        }
    }, redirect_uri, client_id, client_secret


@google_auth_bp.route('/login', methods=['GET'])
@jwt_required()
def google_login():
    """Generate Google OAuth authorization URL.
    Frontend calls this, then redirects the browser to the returned URL.
    
    PKCE: We generate a code_verifier and encode it in the state parameter
    so it survives the redirect and can be restored in the callback.
    """
    db.session.rollback()

    try:
        from google_auth_oauthlib.flow import Flow

        client_config, redirect_uri, client_id, client_secret = _build_client_config()

        if not client_id or not client_secret:
            return jsonify({'error': 'Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.'}), 503

        flow = Flow.from_client_config(client_config, scopes=SCOPES)
        flow.redirect_uri = redirect_uri

        # Generate our own code_verifier for PKCE
        code_verifier = secrets.token_urlsafe(64)

        # Generate code_challenge from verifier for PKCE
        m = hashlib.sha256()
        m.update(code_verifier.encode('ascii'))
        digest = m.digest()
        code_challenge = base64.urlsafe_b64encode(digest).decode('ascii').replace('=', '')

        # Encode user_id AND code_verifier in state so they survive the redirect
        user_id = get_jwt_identity()
        composite_state = f"{user_id}:{code_verifier}"

        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=composite_state,
            code_challenge=code_challenge,
            code_challenge_method='S256',
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
    
    PKCE: Restores the code_verifier from the composite state parameter.
    """
    db.session.rollback()

    try:
        from google_auth_oauthlib.flow import Flow

        code = request.args.get('code')
        state = request.args.get('state')  # composite: "user_id:code_verifier"
        error = request.args.get('error')

        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')

        if error:
            logger.error(f"Google OAuth error: {error}")
            return redirect(f"{frontend_url}/channels?google_error={error}")

        if not code or not state:
            return redirect(f"{frontend_url}/channels?google_error=missing_params")

        # Parse composite state to extract user_id and code_verifier
        if ':' in state:
            user_id_str, code_verifier = state.split(':', 1)
        else:
            # Fallback for legacy state format (just user_id)
            user_id_str = state
            code_verifier = None

        # Rebuild flow
        client_config, redirect_uri, _, _ = _build_client_config()

        flow = Flow.from_client_config(client_config, scopes=SCOPES)
        flow.redirect_uri = redirect_uri

        # Restore the PKCE code_verifier so fetch_token can use it
        if code_verifier:
            flow.code_verifier = code_verifier

        # Allow Google to return additional scopes (e.g. openid, userinfo.profile)
        # beyond what we originally requested — this is normal Google behavior.
        os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

        # Exchange code for tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Save to distributor
        user_id = int(user_id_str)
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


@google_auth_bp.route('/calendars', methods=['GET'])
@jwt_required()
def list_google_calendars():
    """List all Google Calendars for the authenticated distributor."""
    db.session.rollback()

    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user or not user.distributor_id:
            return jsonify({'error': 'User or distributor not found'}), 404

        distributor = Distributor.query.get(user.distributor_id)
        if not distributor or not distributor.google_credentials:
            return jsonify({'error': 'Google not connected'}), 400

        from services.google_service import google_service
        result = google_service.list_calendars(distributor)

        if 'error' in result:
            return jsonify({'error': result['error']}), 400

        return jsonify({
            'data': {
                'calendars': result['calendars'],
                'selected_calendar_id': distributor.google_calendar_id,
            }
        }), 200

    except Exception as e:
        logger.error(f"List calendars error: {e}")
        return jsonify({'error': str(e)}), 500


@google_auth_bp.route('/calendars/select', methods=['POST'])
@jwt_required()
def select_google_calendar():
    """Save the selected Google Calendar ID for the distributor."""
    db.session.rollback()

    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user or not user.distributor_id:
            return jsonify({'error': 'User or distributor not found'}), 404

        distributor = Distributor.query.get(user.distributor_id)
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        data = request.get_json()
        calendar_id = data.get('calendar_id')

        if not calendar_id:
            return jsonify({'error': 'calendar_id is required'}), 400

        distributor.google_calendar_id = calendar_id
        db.session.commit()

        logger.info(f"Calendar {calendar_id} selected for distributor {distributor.id}")
        return jsonify({
            'data': {
                'message': 'Calendar selected successfully',
                'calendar_id': calendar_id,
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Select calendar error: {e}")
        return jsonify({'error': str(e)}), 500


@google_auth_bp.route('/disconnect', methods=['POST'])
@jwt_required()
def google_disconnect():
    """
    Disconnect Google integration — clears credentials and calendar selection.
    Migration Path: Revoke tokens from client-side encrypted vault.
    """
    db.session.rollback()

    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.distributor_id:
            return jsonify({'error': 'User not found'}), 404

        distributor = Distributor.query.get(user.distributor_id)
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        distributor.google_credentials = None
        distributor.google_calendar_id = None
        db.session.commit()

        logger.info(f"Google disconnected for distributor {distributor.id}")
        return jsonify({'data': {'message': 'Google disconnected successfully'}}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Google disconnect error: {e}")
        return jsonify({'error': str(e)}), 500
