"""
Distributor Routes - Settings management for the authenticated distributor.
Migration Path: Distributor config will be stored in user-controlled encrypted vaults.
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.distributor import Distributor

logger = logging.getLogger(__name__)

distributors_bp = Blueprint('distributors', __name__)


def _get_current_distributor():
    """Helper: get the distributor associated with the current JWT user"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user or not user.distributor_id:
        return None, None
    distributor = Distributor.query.get(user.distributor_id)
    return user, distributor


@distributors_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_settings():
    """Get distributor settings"""
    db.session.rollback()

    try:
        user, distributor = _get_current_distributor()
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        return jsonify({'data': distributor.to_dict()}), 200

    except Exception as e:
        logger.error(f"Get settings error: {e}")
        return jsonify({'error': str(e)}), 500


@distributors_bp.route('/settings', methods=['PUT'])
@jwt_required()
def update_settings():
    """Update distributor settings"""
    db.session.rollback()

    try:
        user, distributor = _get_current_distributor()
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Updatable fields
        updatable = [
            'name', 'herbalife_id', 'herbalife_level', 'business_name',
            'timezone', 'language', 'country', 'city', 'email', 'phone',
            'website', 'instagram', 'facebook', 'personal_story'
        ]

        for field in updatable:
            if field in data:
                setattr(distributor, field, data[field])

        db.session.commit()
        logger.info(f"Distributor {distributor.id} settings updated")

        return jsonify({'data': distributor.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update settings error: {e}")
        return jsonify({'error': str(e)}), 500


@distributors_bp.route('/agent-persona', methods=['PUT'])
@jwt_required()
def update_agent_persona():
    """Update the distributor's agent persona (name, gender, personality, instructions)"""
    db.session.rollback()

    try:
        user, distributor = _get_current_distributor()
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        persona_fields = [
            'agent_name', 'agent_gender', 'personality_prompt',
            'custom_instructions', 'llm_provider', 'llm_model'
        ]

        for field in persona_fields:
            if field in data:
                setattr(distributor, field, data[field])

        db.session.commit()
        logger.info(f"Distributor {distributor.id} agent persona updated")

        return jsonify({'data': distributor.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update agent persona error: {e}")
        return jsonify({'error': str(e)}), 500
