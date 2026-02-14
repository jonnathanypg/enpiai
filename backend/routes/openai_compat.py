"""
OpenAI-Compatible Chat Completions Endpoint.
Allows external clients (LibreChat, Typingmind, etc.) to use EnpiAI agents.

Authentication: Bearer token must be a valid distributor API key.
Migration Path: Auth will migrate to DID-based tokens.
"""
from flask import Blueprint, request, jsonify, g
from services.agent_orchestrator import get_agent_orchestrator
from models.distributor import Distributor
from models.conversation import Conversation, Message, MessageRole
from models.customer import Customer
from models.lead import Lead
from extensions import db, limiter
import logging
import uuid
import secrets
from datetime import datetime

openai_bp = Blueprint('openai_compat', __name__)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# API Key Management
# ---------------------------------------------------------------------------

def generate_api_key() -> str:
    """Generate a secure, unique API key for a distributor."""
    return f"enpi-{secrets.token_urlsafe(32)}"


def _authenticate_request():
    """
    Authenticate using Bearer token (distributor API key).
    Returns distributor or (error_response, status_code).
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, (jsonify({"error": {"message": "Authorization required", "type": "auth_error"}}), 401)

    token = auth_header.replace("Bearer ", "").strip()

    if not token or len(token) < 10:
        return None, (jsonify({"error": {"message": "Invalid API Key", "type": "auth_error"}}), 401)

    # Lookup distributor by API key (secure — no enumeration possible)
    distributor = Distributor.query.filter_by(api_key=token, is_active=True).first()
    if not distributor:
        return None, (jsonify({"error": {"message": "Invalid API Key", "type": "auth_error"}}), 401)

    return distributor, None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@openai_bp.route('/v1/chat/completions', methods=['POST'])
@limiter.limit("30 per minute")
def chat_completions():
    """
    OpenAI-compatible chat completions endpoint.
    """
    try:
        db.session.rollback()

        # 1. Authenticate
        distributor, error = _authenticate_request()
        if error:
            return error

        data = request.json
        messages = data.get('messages', [])
        model = data.get('model', 'default')
        user_identifier = data.get('user', 'anonymous')

        if not messages:
            return jsonify({"error": {"message": "messages required", "type": "invalid_request_error"}}), 400

        # 2. Find/Create Conversation
        conversation = Conversation.query.filter_by(
            distributor_id=distributor.id,
            participant_id=user_identifier,
            status='active'
        ).first()

        if not conversation:
            conversation = Conversation(
                distributor_id=distributor.id,
                participant_id=user_identifier,
                channel='api',
                status='active',
                participant_name=user_identifier if '@' in user_identifier else None
            )
            db.session.add(conversation)
            db.session.commit()

        # 3. Get Agent Orchestrator
        orchestrator = get_agent_orchestrator(distributor)

        # 4. Process Message (last user message only — orchestrator manages history)
        last_user_msg = next((m for m in reversed(messages) if m['role'] == 'user'), None)
        if not last_user_msg:
            return jsonify({"error": {"message": "No user message found", "type": "invalid_request_error"}}), 400

        content = last_user_msg['content']

        response_data = orchestrator.process_message(
            conversation=conversation,
            user_message=content,
            channel='api',
            thread_id=f"api_{conversation.id}_{datetime.utcnow().strftime('%Y%m%d')}"
        )

        if response_data.get('error'):
            return jsonify({"error": {"message": response_data.get('content'), "type": "internal_error"}}), 500

        agent_response = response_data.get('content', '')

        # 5. Construct OpenAI Response
        response_id = f"chatcmpl-{uuid.uuid4()}"
        return jsonify({
            "id": response_id,
            "object": "chat.completion",
            "created": int(datetime.utcnow().timestamp()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": agent_response
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        })

    except Exception as e:
        logger.error(f"OpenAI Compat Error: {e}")
        return jsonify({"error": {"message": str(e), "type": "server_error"}}), 500


@openai_bp.route('/v1/models', methods=['GET'])
def list_models():
    """List available models (required for some OpenAI-compatible clients)."""
    return jsonify({
        "object": "list",
        "data": [
            {"id": "enpi-ai", "object": "model", "owned_by": "weblifetech"},
        ]
    })
