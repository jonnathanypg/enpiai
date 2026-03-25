"""
Channel Routes - CRUD for communication channel configurations
+ WhatsApp session management proxy endpoints for api-whatsapp.
Migration Path: Channel credentials will be stored in client-side encrypted vaults.
"""
import os
import logging
import requests as http_requests
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.channel import Channel, ChannelType, ChannelStatus
from models.distributor import Distributor

logger = logging.getLogger(__name__)

channels_bp = Blueprint('channels', __name__)

# WhatsApp API URL (Node.js microservice)
# No longer used, loading from current_app.config in routes
# WHATSAPP_API_URL = os.getenv('WHATSAPP_API_URL', 'http://localhost:3001')


def _get_distributor_id():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    return user.distributor_id if user else None


def _get_distributor():
    """Get the full Distributor object for the authenticated user."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user or not user.distributor_id:
        return None
    return Distributor.query.get(user.distributor_id)


# ═══════════════════════════════════════════════════════════════
# CHANNEL CRUD (existing)
# ═══════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════
# WHATSAPP SESSION MANAGEMENT (proxy to api-whatsapp microservice)
# ═══════════════════════════════════════════════════════════════

@channels_bp.route('/whatsapp/init', methods=['POST'])
@jwt_required()
def init_whatsapp_session():
    """
    Initialize WhatsApp session for the distributor.
    Triggers QR code generation in the api-whatsapp microservice.
    """
    db.session.rollback()

    distributor = _get_distributor()
    if not distributor:
        return jsonify({'error': 'Distributor not found'}), 404

    try:
        whatsapp_url = current_app.config.get('WHATSAPP_API_URL', 'http://localhost:3001')
        response = http_requests.post(
            f"{whatsapp_url}/session/init",
            json={'companyId': str(distributor.id)},
            timeout=30
        )

        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'WhatsApp session started. Please scan the QR code.',
                'session_id': str(distributor.id)
            }), 200
        else:
            return jsonify({
                'error': 'Error starting WhatsApp session',
                'details': response.text
            }), response.status_code

    except http_requests.exceptions.RequestException as e:
        logger.error(f"WhatsApp init error: {e}")
        return jsonify({
            'error': 'Could not connect to WhatsApp service',
            'details': str(e)
        }), 503


@channels_bp.route('/whatsapp/qr', methods=['GET'])
@jwt_required()
def get_whatsapp_qr():
    """
    Get the WhatsApp QR code SVG for scanning.
    """
    db.session.rollback()

    distributor = _get_distributor()
    if not distributor:
        return jsonify({'error': 'Distributor not found'}), 404

    try:
        whatsapp_url = current_app.config.get('WHATSAPP_API_URL', 'http://localhost:3001')
        response = http_requests.get(
            f"{whatsapp_url}/session/qr/{distributor.id}",
            timeout=30
        )

        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'json' in content_type:
                # JSON response (e.g., {"status": "connected"} when already paired)
                try:
                    data = response.json()
                    return jsonify(data), 200
                except Exception:
                    pass

            # Raw SVG response — wrap in JSON for the frontend
            svg_content = response.text
            return jsonify({'qr': svg_content, 'success': True}), 200
        else:
            return jsonify({
                'error': 'QR not available',
                'details': response.text
            }), response.status_code

    except http_requests.exceptions.RequestException as e:
        logger.error(f"WhatsApp QR error: {e}")
        return jsonify({
            'error': 'Could not get QR code',
            'details': str(e)
        }), 503


@channels_bp.route('/whatsapp/status', methods=['GET'])
@jwt_required()
def get_whatsapp_status():
    """
    Get WhatsApp connection status.
    """
    db.session.rollback()

    distributor = _get_distributor()
    if not distributor:
        return jsonify({'error': 'Distributor not found'}), 404

    try:
        whatsapp_url = current_app.config.get('WHATSAPP_API_URL', 'http://localhost:3001')
        response = http_requests.get(
            f"{whatsapp_url}/session/status/{distributor.id}",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            is_connected = data.get('status') == 'open' or data.get('connected') == True

            # Sync local state
            if distributor.whatsapp_connected != is_connected:
                distributor.whatsapp_connected = is_connected
                db.session.commit()

            return jsonify({
                'connected': is_connected,
                'phone': distributor.whatsapp_phone,
                'status': data.get('status') or data.get('state')
            }), 200
        else:
            return jsonify({
                'connected': False,
                'status': 'disconnected'
            }), 200

    except http_requests.exceptions.RequestException:
        return jsonify({
            'connected': distributor.whatsapp_connected,
            'phone': distributor.whatsapp_phone,
            'status': 'unknown'
        }), 200


@channels_bp.route('/whatsapp/disconnect', methods=['POST'])
@jwt_required()
def disconnect_whatsapp():
    """
    Disconnect WhatsApp session.
    """
    db.session.rollback()

    distributor = _get_distributor()
    if not distributor:
        return jsonify({'error': 'Distributor not found'}), 404

    try:
        whatsapp_url = current_app.config.get('WHATSAPP_API_URL', 'http://localhost:3001')
        http_requests.post(
            f"{whatsapp_url}/session/logout",
            json={'companyId': str(distributor.id)},
            timeout=30
        )
    except http_requests.exceptions.RequestException as e:
        logger.warning(f"WhatsApp disconnect warning: {e}")

    # Always update local state
    distributor.whatsapp_connected = False
    distributor.whatsapp_phone = None
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'WhatsApp disconnected'
    }), 200
