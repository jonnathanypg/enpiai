"""
Channel Routes - CRUD for communication channel configurations.
Migration Path: Channel credentials will be stored in client-side encrypted vaults.
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.channel import Channel, ChannelType, ChannelStatus

logger = logging.getLogger(__name__)

channels_bp = Blueprint('channels', __name__)


def _get_distributor_id():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    return user.distributor_id if user else None


@channels_bp.route('', methods=['GET'])
@jwt_required()
def list_channels():
    """List all channels for the distributor"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        if not distributor_id:
            return jsonify({'error': 'Distributor not found'}), 404

        channels = Channel.query.filter_by(distributor_id=distributor_id).all()
        return jsonify({'data': [c.to_dict() for c in channels]}), 200

    except Exception as e:
        logger.error(f"List channels error: {e}")
        return jsonify({'error': str(e)}), 500


@channels_bp.route('', methods=['POST'])
@jwt_required()
def create_channel():
    """Create a new channel configuration"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        if not distributor_id:
            return jsonify({'error': 'Distributor not found'}), 404

        data = request.get_json()
        if not data or not data.get('channel_type') or not data.get('name'):
            return jsonify({'error': 'channel_type and name are required'}), 400

        channel = Channel(
            distributor_id=distributor_id,
            channel_type=data['channel_type'],
            name=data['name'],
            config=data.get('config', {}),
            credentials=data.get('credentials', {}),
        )
        db.session.add(channel)
        db.session.commit()

        logger.info(f"Channel created: {channel.name} ({channel.channel_type.value})")
        return jsonify({'data': channel.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Create channel error: {e}")
        return jsonify({'error': str(e)}), 500


@channels_bp.route('/<int:channel_id>', methods=['GET'])
@jwt_required()
def get_channel(channel_id):
    """Get a single channel"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        channel = Channel.query.filter_by(id=channel_id, distributor_id=distributor_id).first()
        if not channel:
            return jsonify({'error': 'Channel not found'}), 404

        return jsonify({'data': channel.to_dict(include_credentials=True)}), 200

    except Exception as e:
        logger.error(f"Get channel error: {e}")
        return jsonify({'error': str(e)}), 500


@channels_bp.route('/<int:channel_id>', methods=['PUT'])
@jwt_required()
def update_channel(channel_id):
    """Update a channel configuration"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        channel = Channel.query.filter_by(id=channel_id, distributor_id=distributor_id).first()
        if not channel:
            return jsonify({'error': 'Channel not found'}), 404

        data = request.get_json()
        if 'name' in data:
            channel.name = data['name']
        if 'config' in data:
            channel.config = data['config']
        if 'credentials' in data:
            channel.credentials = data['credentials']
        if 'status' in data:
            channel.status = data['status']

        db.session.commit()
        return jsonify({'data': channel.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update channel error: {e}")
        return jsonify({'error': str(e)}), 500


@channels_bp.route('/<int:channel_id>', methods=['DELETE'])
@jwt_required()
def delete_channel(channel_id):
    """Delete a channel"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        channel = Channel.query.filter_by(id=channel_id, distributor_id=distributor_id).first()
        if not channel:
            return jsonify({'error': 'Channel not found'}), 404

        db.session.delete(channel)
        db.session.commit()

        return jsonify({'data': {'message': 'Channel deleted successfully'}}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete channel error: {e}")
        return jsonify({'error': str(e)}), 500
