"""
Agent Config Routes - CRUD for agent configurations and feature toggles.
Migration Path: Agent config will be stored in user-controlled encrypted vaults.
"""
import logging
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.agent_config import AgentConfig, AgentFeature, DEFAULT_FEATURES
from models.distributor import Distributor
from models.conversation import Conversation

logger = logging.getLogger(__name__)

agents_bp = Blueprint('agents', __name__)


def _get_distributor_id():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    return user.distributor_id if user else None


@agents_bp.route('', methods=['GET'])
@jwt_required()
def list_agents():
    """List all agent configs for the distributor"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        if not distributor_id:
            return jsonify({'error': 'Distributor not found'}), 404

        agents = AgentConfig.query.filter_by(distributor_id=distributor_id).all()
        return jsonify({'data': [a.to_dict() for a in agents]}), 200

    except Exception as e:
        logger.error(f"List agents error: {e}")
        return jsonify({'error': str(e)}), 500


@agents_bp.route('', methods=['POST'])
@jwt_required()
def create_agent():
    """Create a new agent configuration"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        if not distributor_id:
            return jsonify({'error': 'Distributor not found'}), 404

        data = request.get_json()
        if not data or not data.get('name'):
            return jsonify({'error': 'Agent name is required'}), 400

        agent = AgentConfig(
            distributor_id=distributor_id,
            name=data['name'],
            description=data.get('description'),
            agent_type=data.get('agent_type', 'prospect'),
            tone=data.get('tone', 'friendly'),
            objective=data.get('objective', 'general'),
            system_prompt=data.get('system_prompt'),
        )
        db.session.add(agent)
        db.session.flush()

        # Initialize default features
        for feat_data in DEFAULT_FEATURES:
            feature = AgentFeature(
                agent_id=agent.id,
                category=feat_data['category'],
                name=feat_data['name'],
                label=feat_data['label'],
                description=feat_data.get('description', ''),
                order=feat_data.get('order', 0),
                is_enabled=False
            )
            db.session.add(feature)

        db.session.commit()

        logger.info(f"Agent created: {agent.name} for distributor {distributor_id}")
        return jsonify({'data': agent.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Create agent error: {e}")
        return jsonify({'error': str(e)}), 500


@agents_bp.route('/<int:agent_id>', methods=['GET'])
@jwt_required()
def get_agent(agent_id):
    """Get a single agent config"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        agent = AgentConfig.query.filter_by(id=agent_id, distributor_id=distributor_id).first()
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404

        return jsonify({'data': agent.to_dict()}), 200

    except Exception as e:
        logger.error(f"Get agent error: {e}")
        return jsonify({'error': str(e)}), 500


@agents_bp.route('/<int:agent_id>', methods=['PUT'])
@jwt_required()
def update_agent(agent_id):
    """Update agent configuration"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        agent = AgentConfig.query.filter_by(id=agent_id, distributor_id=distributor_id).first()
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404

        data = request.get_json()
        updatable = ['name', 'description', 'agent_type', 'tone', 'objective', 'system_prompt', 'priority', 'is_active']

        for field in updatable:
            if field in data:
                setattr(agent, field, data[field])

        db.session.commit()
        return jsonify({'data': agent.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update agent error: {e}")
        return jsonify({'error': str(e)}), 500


@agents_bp.route('/<int:agent_id>', methods=['DELETE'])
@jwt_required()
def delete_agent(agent_id):
    """Delete an agent config and all its features"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        agent = AgentConfig.query.filter_by(id=agent_id, distributor_id=distributor_id).first()
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404

        db.session.delete(agent)
        db.session.commit()

        return jsonify({'data': {'message': 'Agent deleted successfully'}}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete agent error: {e}")
        return jsonify({'error': str(e)}), 500


@agents_bp.route('/<int:agent_id>/features', methods=['PUT'])
@jwt_required()
def update_features(agent_id):
    """Batch update feature toggles for an agent.
    Expects: { "features": { "whatsapp": true, "telegram": false, ... } }
    """
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        agent = AgentConfig.query.filter_by(id=agent_id, distributor_id=distributor_id).first()
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404

        data = request.get_json()
        features_update = data.get('features', {})

        for feature_name, is_enabled in features_update.items():
            feature = AgentFeature.query.filter_by(
                agent_id=agent.id, name=feature_name
            ).first()
            if feature:
                feature.is_enabled = bool(is_enabled)

        db.session.commit()

        return jsonify({'data': agent.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update features error: {e}")
        return jsonify({'error': str(e)}), 500


# =========================================================================
# Playground Chat (JWT-authenticated)
# =========================================================================

@agents_bp.route('/chat', methods=['POST'])
@jwt_required()
def playground_chat():
    """Chat with the agent from the frontend playground.
    Uses JWT auth (dashboard user) instead of API key.
    """
    db.session.rollback()
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user or not user.distributor_id:
            return jsonify({'error': {'message': 'Distributor context required'}}), 403

        distributor = Distributor.query.get(user.distributor_id)
        if not distributor:
            return jsonify({'error': {'message': 'Distributor not found'}}), 404

        data = request.get_json()
        messages = data.get('messages', [])
        user_identifier = data.get('user', f'playground_{user_id}')

        if not messages:
            return jsonify({'error': {'message': 'messages required'}}), 400

        # Find or create conversation for playground
        conversation = Conversation.query.filter_by(
            distributor_id=distributor.id,
            participant_id=user_identifier,
            channel='playground',
            status='active'
        ).first()

        if not conversation:
            conversation = Conversation(
                distributor_id=distributor.id,
                participant_id=user_identifier,
                channel='playground',
                status='active',
                participant_name=user.name or user.email
            )
            db.session.add(conversation)
            db.session.commit()

        # Get orchestrator
        from services.agent_orchestrator import get_agent_orchestrator
        orchestrator = get_agent_orchestrator(distributor)

        # Process last user message
        last_user_msg = next((m for m in reversed(messages) if m['role'] == 'user'), None)
        if not last_user_msg:
            return jsonify({'error': {'message': 'No user message found'}}), 400

        response_data = orchestrator.process_message(
            conversation=conversation,
            user_message=last_user_msg['content'],
            channel='playground',
            thread_id=f"playground_{conversation.id}_{datetime.utcnow().strftime('%Y%m%d')}"
        )

        if response_data.get('error'):
            return jsonify({'error': {'message': response_data.get('content')}}), 500

        agent_response = response_data.get('content', '')

        return jsonify({
            'id': f'chatcmpl-{uuid.uuid4()}',
            'object': 'chat.completion',
            'created': int(datetime.utcnow().timestamp()),
            'choices': [{
                'index': 0,
                'message': {'role': 'assistant', 'content': agent_response},
                'finish_reason': 'stop'
            }]
        }), 200

    except Exception as e:
        logger.error(f"Playground chat error: {e}")
        return jsonify({'error': {'message': str(e)}}), 500
