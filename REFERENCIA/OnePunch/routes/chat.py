"""
Admin Chat Routes
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import emit, join_room
from extensions import db, socketio
from models.user import User
from models.conversation import Conversation, Message, ConversationType, MessageChannel, MessageRole

chat_bp = Blueprint('chat', __name__)


def get_user_company():
    """Helper to get current user's company"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or not user.company:
            print(f"DEBUG: Chat - User/Company missing for ID {user_id}")
            return None, None
        return user, user.company
    except Exception as e:
        print(f"DEBUG: Chat - Error: {e}")
        return None, None


@chat_bp.route('/conversations', methods=['GET'])
@jwt_required()
def list_conversations():
    """List all conversations"""
    user, company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    # Filter parameters
    conversation_type = request.args.get('type')
    channel = request.args.get('channel')
    is_active = request.args.get('active', 'true').lower() == 'true'
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Conversation.query.filter_by(company_id=company.id)
    
    if conversation_type:
        try:
            query = query.filter_by(type=ConversationType(conversation_type))
        except ValueError:
            pass
    
    if channel:
        try:
            query = query.filter_by(channel=MessageChannel(channel))
        except ValueError:
            pass
    
    if is_active is not None:
        query = query.filter_by(is_active=is_active)
    
    query = query.order_by(Conversation.last_message_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'conversations': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@chat_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation(conversation_id):
    """Get conversation with messages"""
    user, company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    conversation = Conversation.query.filter_by(
        id=conversation_id,
        company_id=company.id
    ).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    return jsonify({'conversation': conversation.to_dict(include_messages=True)})


@chat_bp.route('/admin', methods=['GET'])
@jwt_required()
def get_admin_chat():
    """Get or create admin chat conversation"""
    user, company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    # Find or create admin chat conversation
    conversation = Conversation.query.filter_by(
        company_id=company.id,
        type=ConversationType.ADMIN,
        channel=MessageChannel.ADMIN_CHAT,
        contact_email=user.email
    ).first()
    
    if not conversation:
        conversation = Conversation(
            company_id=company.id,
            type=ConversationType.ADMIN,
            channel=MessageChannel.ADMIN_CHAT,
            contact_name=user.name,
            contact_email=user.email
        )
        db.session.add(conversation)
        db.session.commit()
    
    return jsonify({'conversation': conversation.to_dict(include_messages=True)})


@chat_bp.route('/admin/message', methods=['POST'])
@jwt_required()
def send_admin_message():
    """Send message in admin chat"""
    user, company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    data = request.get_json()
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Message content is required'}), 400
    
    # Get or create admin chat conversation
    conversation = Conversation.query.filter_by(
        company_id=company.id,
        type=ConversationType.ADMIN,
        channel=MessageChannel.ADMIN_CHAT,
        contact_email=user.email
    ).first()
    
    if not conversation:
        conversation = Conversation(
            company_id=company.id,
            type=ConversationType.ADMIN,
            channel=MessageChannel.ADMIN_CHAT,
            contact_name=user.name,
            contact_email=user.email
        )
        db.session.add(conversation)
        db.session.flush()
    
    # Create user message
    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=content,
        channel=MessageChannel.ADMIN_CHAT
    )
    db.session.add(user_message)
    
    # Update conversation timestamp
    conversation.last_message_at = datetime.utcnow()
    
    db.session.commit()
    
    # Generate AI response using agent service
    try:
        from services.agent_service import AgentService
        agent_service = AgentService(company)
        
        # Process message using the company's active agent
        response_data = agent_service.process_message(
            conversation=conversation,
            user_message=content,
            channel='admin_chat'
        )
        
        assistant_response = response_data.get('content')
        
        # If content is None but we have tool calls, provide a status update
        if not assistant_response and response_data.get('tool_calls'):
            tool_names = [t.get('tool', 'unknown') for t in response_data['tool_calls']]
            assistant_response = f"I am performing the following actions: {', '.join(tool_names)}..."
            print(f"DEBUG: Agent executing tools: {tool_names}")
            
        # Fallback if still None
        if not assistant_response:
            assistant_response = "I apologize, but I couldn't generate a verbal response."

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR: Failed to generate AI response: {e}")
        assistant_response = "I apologize, but I'm having trouble connecting to my brain right now. Please check your API configuration."

    assistant_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=assistant_response,
        channel=MessageChannel.ADMIN_CHAT,
        tool_calls=response_data.get('tool_calls', []) if 'response_data' in locals() else []
    )
    db.session.add(assistant_message)
    conversation.last_message_at = datetime.utcnow()
    db.session.commit()
    
    # Debug print for terminal visibility
    print(f"\n[AI RESPONSE] >>> {assistant_response}")
    if 'response_data' in locals() and response_data.get('tool_calls'):
        print(f"[AI TOOLS] >>> {response_data['tool_calls']}\n")
    
    return jsonify({
        'user_message': user_message.to_dict(),
        'assistant_message': assistant_message.to_dict()
    })


@chat_bp.route('/history', methods=['GET'])
@jwt_required()
def get_chat_history():
    """Get chat history for current user"""
    user, company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    # Get admin chat history
    conversation = Conversation.query.filter_by(
        company_id=company.id,
        type=ConversationType.ADMIN,
        channel=MessageChannel.ADMIN_CHAT,
        contact_email=user.email
    ).first()
    
    if not conversation:
        return jsonify({'messages': []})
    
    messages = Message.query.filter_by(
        conversation_id=conversation.id
    ).order_by(Message.created_at).all()
    
    return jsonify({'messages': [m.to_dict() for m in messages]})


# WebSocket events for real-time chat
@socketio.on('join_chat')
def handle_join_chat(data):
    """Join a chat room"""
    room = f"chat_{data.get('conversation_id')}"
    join_room(room)
    emit('joined', {'room': room})


@socketio.on('send_message')
def handle_send_message(data):
    """Handle real-time message sending"""
    conversation_id = data.get('conversation_id')
    content = data.get('content')
    
    if not conversation_id or not content:
        return
    
    room = f"chat_{conversation_id}"
    
    # Emit to all clients in the room
    emit('new_message', {
        'conversation_id': conversation_id,
        'content': content,
        'role': 'user',
        'timestamp': datetime.utcnow().isoformat()
    }, room=room)
