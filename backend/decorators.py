"""
Decorators - Access control middleware for the SaaS platform.
Provides route guards for subscription status and Super Admin access.

Migration Path: Access control will be verified via cryptographic proofs.
"""
import logging
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from extensions import db

logger = logging.getLogger(__name__)


def subscription_required(f):
    """
    Decorator to verify the current user's distributor has an active subscription.
    Must be used AFTER @jwt_required().
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        db.session.rollback()
        try:
            from models.user import User
            from models.subscription import Subscription

            user_id = get_jwt_identity()
            user = User.query.get(int(user_id))

            if not user or not user.distributor_id:
                return jsonify({'error': 'Distributor context required'}), 403

            # Super Admins bypass subscription checks
            from models.user import UserRole
            if user.role == UserRole.SUPER_ADMIN:
                return f(*args, **kwargs)

            subscription = Subscription.query.filter_by(
                distributor_id=user.distributor_id
            ).first()

            if not subscription or not subscription.is_active:
                return jsonify({
                    'error': 'Active subscription required',
                    'code': 'SUBSCRIPTION_REQUIRED'
                }), 402  # 402 Payment Required

            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Subscription check error: {e}")
            return jsonify({'error': 'Subscription verification failed'}), 500

    return decorated_function


def super_admin_required(f):
    """
    Decorator to restrict access to Super Admin users only.
    Must be used AFTER @jwt_required().
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        db.session.rollback()
        try:
            from models.user import User, UserRole

            user_id = get_jwt_identity()
            user = User.query.get(int(user_id))

            if not user or user.role != UserRole.SUPER_ADMIN:
                return jsonify({'error': 'Super Admin access required'}), 403

            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Super admin check error: {e}")
            return jsonify({'error': 'Authorization failed'}), 500

    return decorated_function
