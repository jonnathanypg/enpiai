"""
Authentication Routes
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, verify_jwt_in_request
)
from extensions import db
from models.user import User, UserRole
from models.company import Company

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/debug-token', methods=['GET'])
def debug_token():
    """Debug endpoint to check token"""
    from flask import current_app
    auth_header = request.headers.get('Authorization', 'No Authorization header')
    jwt_secret = current_app.config.get('JWT_SECRET_KEY', 'NOT SET')
    
    # Show first 10 chars of secret for debugging
    secret_preview = jwt_secret[:10] + '...' if len(jwt_secret) > 10 else jwt_secret
    
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        return jsonify({
            'header_received': auth_header,
            'user_id': user_id,
            'status': 'valid',
            'jwt_secret_preview': secret_preview
        })
    except Exception as e:
        return jsonify({
            'header_received': auth_header,
            'error': str(e),
            'error_type': type(e).__name__,
            'status': 'invalid',
            'jwt_secret_preview': secret_preview
        }), 401


@auth_bp.route('/debug-create-token', methods=['GET'])
def debug_create_token():
    """Debug endpoint to create and immediately verify a test token"""
    from flask import current_app
    
    jwt_secret = current_app.config.get('JWT_SECRET_KEY', 'NOT SET')
    secret_preview = jwt_secret[:10] + '...' if len(jwt_secret) > 10 else jwt_secret
    
    # Create a test token
    test_token = create_access_token(identity=999)
    
    # Try to verify it immediately
    try:
        # Manually decode to check
        import jwt as pyjwt
        decoded = pyjwt.decode(test_token, jwt_secret, algorithms=['HS256'])
        return jsonify({
            'test_token': test_token[:50] + '...',
            'decoded': decoded,
            'jwt_secret_preview': secret_preview,
            'status': 'Token created and verified successfully'
        })
    except Exception as e:
        return jsonify({
            'test_token': test_token[:50] + '...',
            'error': str(e),
            'jwt_secret_preview': secret_preview,
            'status': 'Token verification failed'
        }), 500


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user and company"""
    data = request.get_json()
    
    # Validate required fields
    required = ['email', 'password', 'name', 'company_name']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if user exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    try:
        # Create company
        company = Company(
            name=data['company_name'],
            agent_name=data.get('agent_name', 'Assistant'),
            industry=data.get('industry'),
            language=data.get('language', 'en')
        )
        db.session.add(company)
        db.session.flush()
        
        # Create user
        user = User(
            email=data['email'],
            name=data['name'],
            role=UserRole.ADMIN,
            company_id=company.id
        )
        user.set_password(data['password'])
        db.session.add(user)
        
        db.session.commit()
        
        # Generate tokens (identity must be string for JWT compatibility)
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Registration successful',
            'user': user.to_dict(),
            'company': company.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is disabled'}), 403
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Generate tokens (identity must be string for JWT compatibility)
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'company': user.company.to_dict() if user.company else None,
        'access_token': access_token,
        'refresh_token': refresh_token
    })


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    user_id = get_jwt_identity()  # Already a string
    access_token = create_access_token(identity=user_id)
    return jsonify({'access_token': access_token})


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    user_id = int(get_jwt_identity())  # Convert string back to int
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user': user.to_dict(),
        'company': user.company.to_dict() if user.company else None
    })


@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    """Update current user info"""
    user_id = int(get_jwt_identity())  # Convert string back to int
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if data.get('name'):
        user.name = data['name']
    
    if data.get('password'):
        user.set_password(data['password'])
    
    db.session.commit()
    
    return jsonify({
        'message': 'User updated',
        'user': user.to_dict()
    })
