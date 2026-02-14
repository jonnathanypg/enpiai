"""
Auth Routes - Registration, Login, JWT refresh, user info.
Migration Path: Auth will migrate to DID-based cryptographic key exchange.
"""
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from extensions import db, limiter
from models.user import User, UserRole
from models.distributor import Distributor
from models.agent_config import AgentConfig, AgentFeature, DEFAULT_FEATURES
from services.i18n_service import i18n_service

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("3 per minute")
def register():
    """Register a new distributor and admin user"""
    db.session.rollback()  # Preventive rollback (GEMINI.md Rule B.1)

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Required fields
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        distributor_name = data.get('distributor_name', '').strip()

        if not all([email, password, name, distributor_name]):
            return jsonify({'error': 'Email, password, name, and distributor_name are required'}), 400

        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'An account with this email already exists'}), 409

        # Create distributor (tenant)
        distributor = Distributor(
            name=distributor_name,
            herbalife_id=data.get('herbalife_id'),
            email=email,
            phone=data.get('phone'),
            country=data.get('country'),
            city=data.get('city'),
            language=data.get('language', 'en')  # Default to English
        )
        db.session.add(distributor)
        db.session.flush()  # Get distributor ID

        # Create admin user
        user = User(
            email=email,
            name=name,
            role=UserRole.ADMIN,
            distributor_id=distributor.id
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        # Create default Prospect Agent (Localized)
        default_agent_data = i18n_service.get_default_agent_data(distributor.language)
        
        prospect_agent = AgentConfig(
            distributor_id=distributor.id,
            name=default_agent_data['name'],
            description=default_agent_data['description'],
            agent_type='prospect',
            is_active=True
        )
        db.session.add(prospect_agent)
        db.session.flush()

        # Initialize default features for the agent
        for feat_data in DEFAULT_FEATURES:
            feature = AgentFeature(
                agent_id=prospect_agent.id,
                category=feat_data['category'],
                name=feat_data['name'],
                label=feat_data['label'],
                description=feat_data.get('description', ''),
                order=feat_data.get('order', 0),
                is_enabled=feat_data['name'] in ['whatsapp', 'knowledge_base_search', 'wellness_evaluation', 'conversation_history']
            )
            db.session.add(feature)

        db.session.commit()

        # Generate tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        logger.info(f"New distributor registered: {distributor_name} ({email})")

        return jsonify({
            'data': {
                'user': user.to_dict(),
                'distributor': distributor.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {e}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Login with email and password"""
    db.session.rollback()

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401

        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 403

        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Generate tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        logger.info(f"User logged in: {email}")

        return jsonify({
            'data': {
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Login error: {e}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    db.session.rollback()

    try:
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=current_user_id)

        return jsonify({
            'data': {'access_token': access_token}
        }), 200

    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user info"""
    db.session.rollback()

    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))

        if not user:
            return jsonify({'error': 'User not found'}), 404

        response = user.to_dict()

        # Include distributor info if available
        if user.distributor:
            response['distributor'] = user.distributor.to_dict()

        return jsonify({'data': response}), 200

    except Exception as e:
        logger.error(f"Get user error: {e}")
        return jsonify({'error': str(e)}), 500


def get_current_distributor():
    """Helper to get distributor from current JWT user"""
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return None
            
        user = User.query.get(int(user_id))
        return user.distributor if user else None
    except Exception:
        return None
