import logging
import random
import string
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models.user import User, UserRole
from models.distributor import Distributor
from models.subscription import Plan, Subscription, SubscriptionStatus, PlanInterval
from services.dlocal_service import DLocalGoService
from services.email_service import email_service
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)
billing_bp = Blueprint('billing', __name__, url_prefix='/api/billing')
dlocal_service = DLocalGoService()


def admin_required(fn):
    """Decorator to require super admin access."""
    def wrapper(*args, **kwargs):
        db.session.rollback()
        identity = get_jwt_identity()
        # Identity comes as a plain string (user id) from create_access_token
        user = User.query.get(int(identity))
        if not user or user.role != UserRole.SUPER_ADMIN:
            return jsonify({"error": "Admin privileges required"}), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


# ──────────────────────────────────────────────
# PLANS — CRUD
# ──────────────────────────────────────────────


@billing_bp.route('/plans', methods=['GET'])
def get_plans():
    """Returns all active plans."""
    try:
        db.session.rollback()
        plans = Plan.query.filter_by(is_active=True).all()
        return jsonify([p.to_dict() for p in plans]), 200
    except Exception as e:
        logger.error(f"Error fetching plans: {e}")
        return jsonify({"error": str(e)}), 500


@billing_bp.route('/plans', methods=['POST'])
@jwt_required()
@admin_required
def create_plan():
    """Create a new plan in both dLocal Go and local DB."""
    data = request.json
    try:
        name = data.get('name')
        description = data.get('description', '')
        amount = data.get('amount')
        currency = data.get('currency', 'USD')
        frequency_type = data.get('frequency_type', 'MONTHLY')
        
        # 1. Try to create in dLocal Go (will fail silently if keys are not set)
        plan_token = None
        dlocal_plan_id = None
        try:
            dlocal_resp = dlocal_service.create_plan(
                name=name,
                description=description,
                amount=amount,
                currency=currency,
                frequency_type=frequency_type
            )
            plan_token = dlocal_resp.get('plan_token')
            dlocal_plan_id = str(dlocal_resp.get('id', ''))
        except Exception as dlocal_err:
            logger.warning(f"dLocal Go plan creation skipped: {dlocal_err}")
            
        # 2. Save in DB (always)
        features = data.get('features', {
            "analytics_enabled": False,
            "channels": "whatsapp",
            "max_agents": 1,
            "max_documents": 10,
            "max_leads": 100,
            "rag_enabled": True
        })
        
        new_plan = Plan(
            name=name,
            description=description,
            price_monthly=amount if frequency_type == 'MONTHLY' else 0,
            price_annual=amount if frequency_type == 'YEARLY' else 0,
            currency=currency,
            dlocal_plan_id=dlocal_plan_id,
            dlocal_plan_token=plan_token,
            is_active=True,
            features=features
        )
        db.session.add(new_plan)
        db.session.commit()
        
        return jsonify(new_plan.to_dict()), 201

    except Exception as e:
        logger.error(f"Error creating plan: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@billing_bp.route('/plans/<int:plan_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_plan(plan_id):
    """Update an existing plan."""
    data = request.json
    try:
        plan = Plan.query.get(plan_id)
        if not plan:
            return jsonify({"error": "Plan not found"}), 404

        dlocal_payload = {}
        if 'name' in data:
            plan.name = data['name']
            dlocal_payload['name'] = plan.name
        if 'description' in data:
            plan.description = data['description']
            dlocal_payload['description'] = plan.description
        if 'amount' in data:
            plan.price_monthly = data['amount']
            dlocal_payload['amount'] = plan.price_monthly
        if 'price_monthly' in data:
            plan.price_monthly = data['price_monthly']
            dlocal_payload['amount'] = plan.price_monthly
        if 'price_annual' in data:
            plan.price_annual = data['price_annual']
        if 'currency' in data:
            plan.currency = data['currency']
        if 'is_active' in data:
            plan.is_active = data['is_active']
        if 'is_default' in data:
            # If marking as default, un-default all others first
            if data['is_default']:
                Plan.query.update({Plan.is_default: False})
            plan.is_default = data['is_default']
        if 'features' in data:
            plan.features = data['features']

        # Sync changes with dLocal Go if applicable
        if dlocal_payload and plan.dlocal_plan_id:
            try:
                dlocal_service.update_plan(
                    plan_id=plan.dlocal_plan_id,
                    name=dlocal_payload.get('name'),
                    description=dlocal_payload.get('description'),
                    amount=dlocal_payload.get('amount')
                )
            except Exception as e:
                logger.error(f"Error syncing updated plan {plan.id} with dLocal Go: {e}")
                # We log the error but do not fail the local DB update

        db.session.commit()
        return jsonify(plan.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating plan: {e}")
        return jsonify({"error": str(e)}), 500


@billing_bp.route('/plans/<int:plan_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_plan(plan_id):
    """Soft-delete a plan (mark inactive)."""
    try:
        plan = Plan.query.get(plan_id)
        if not plan:
            return jsonify({"error": "Plan not found"}), 404

        plan.is_active = False
        db.session.commit()
        return jsonify({"message": f"Plan '{plan.name}' deactivated"}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting plan: {e}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# SUBSCRIBE (Distributor)
# ──────────────────────────────────────────────


@billing_bp.route('/subscribe', methods=['POST'])
@jwt_required()
def get_checkout_url():
    """
    Given a valid plan_id, returns the specific dLocal checkout URL 
    tailored to the currently authenticated distributor.
    """
    db.session.rollback()
    data = request.json
    plan_id = data.get('plan_id')
    
    if not plan_id:
        return jsonify({'error': 'plan_id is required'}), 400
        
    identity = get_jwt_identity()
    user = User.query.get(int(identity))
    distributor = user.distributor
    
    if not distributor:
        return jsonify({'error': 'No distributor attached to this user'}), 400

    plan = Plan.query.get(plan_id)
    if not plan or not plan.dlocal_plan_token:
        return jsonify({'error': 'Plan not found or not linked to dLocal Go yet'}), 404
        
    try:
        # Generate Checkout URL with their distributor ID
        checkout_url = dlocal_service.get_checkout_url(
            plan_token=plan.dlocal_plan_token,
            distributor_id=distributor.id,
            email=user.email
        )
        return jsonify({'subscribe_url': checkout_url}), 200
        
    except Exception as e:
        logger.error(f"Subscribe error: {e}")
        return jsonify({'error': str(e)}), 500


@billing_bp.route('/my-subscription', methods=['GET'])
@jwt_required()
def get_my_subscription():
    """
    Returns the current distributor's active subscription details.
    """
    db.session.rollback()
    identity = get_jwt_identity()
    user = User.query.get(int(identity))
    distributor = user.distributor
    
    if not distributor:
        return jsonify({'error': 'No distributor attached to this user'}), 400

    # 1. Check if it's a courtesy account
    if distributor.is_courtesy:
        # Mock a subscription object for courtesy users
        # Find the default plan to show what features they have
        plan = Plan.query.filter_by(is_default=True).first()
        if not plan:
            plan = Plan.query.first() # Fallback
            
        return jsonify({
            'status': 'courtesy',
            'is_active': True,
            'plan_name': plan.name if plan else 'Courtesy',
            'plan_description': plan.description if plan else 'Premium features enabled',
            'price': 0,
            'currency': 'USD',
            'features': plan.features if plan else {},
            'start_date': distributor.created_at.isoformat() if distributor.created_at else None,
            'next_payment_at': None,
            'notes': 'Courtesy account granted by administrator'
        }), 200

    # 2. Check for an actual subscription record
    # Since dLocal subscriptions are asynchronous, we might have distributor.subscription_plan_id
    # but not a row in the 'subscriptions' table yet, or vice versa.
    sub = Subscription.query.filter_by(distributor_id=distributor.id).order_by(Subscription.created_at.desc()).first()
    
    if not sub:
        # Check if they have a plan_id assigned but no record (should be rare)
        if distributor.subscription_plan_id:
            plan = Plan.query.get(distributor.subscription_plan_id)
            return jsonify({
                'status': 'pending',
                'is_active': distributor.subscription_active,
                'plan_name': plan.name,
                'plan_description': plan.description,
                'price': plan.price_monthly,
                'currency': plan.currency,
                'features': plan.features,
                'start_date': None,
                'next_payment_at': None
            }), 200
            
        return jsonify({'status': 'none', 'is_active': False}), 200

    return jsonify({
        'status': sub.status.value,
        'is_active': sub.is_active,
        'plan_name': sub.plan.name if sub.plan else 'Unknown',
        'plan_description': sub.plan.description if sub.plan else '',
        'price': sub.plan.price_monthly if sub.plan else 0,
        'currency': sub.plan.currency if sub.plan else 'USD',
        'features': sub.plan.features if sub.plan else {},
        'start_date': sub.start_date.isoformat() if sub.start_date else None,
        'next_payment_at': sub.next_payment_at.isoformat() if sub.next_payment_at else None,
        'notes': sub.notes
    }), 200


# ──────────────────────────────────────────────
# COURTESY ACCOUNTS (Super Admin)
# ──────────────────────────────────────────────


@billing_bp.route('/courtesy-account', methods=['POST'])
@jwt_required()
@admin_required
def create_courtesy_account():
    """
    Creates a new distributor and user with 'is_courtesy=True', bypassing billing.
    Returns the temporary credentials.
    """
    data = request.json
    email = data.get('email')
    name = data.get('name', 'Distributor Courtesy')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
        
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400
        
    try:
        # Generate temp password
        chars = string.ascii_letters + string.digits
        temp_pass = ''.join(random.choice(chars) for _ in range(10))
        
        # Create distributor explicitly as courtesy
        distributor = Distributor(
            name=name,
            email=email,
            is_courtesy=True,
            subscription_active=True  # Treat them as active
        )
        db.session.add(distributor)
        db.session.flush()  # Get ID
        
        # Create user
        user = User(
            email=email,
            name=name,
            role=UserRole.ADMIN,
            distributor_id=distributor.id
        )
        user.set_password(temp_pass)
        
        db.session.add(user)
        db.session.commit()

        # Send courtesy account credentials email
        try:
            email_service.send_courtesy_account_created(email, name, temp_pass, lang=distributor.language or 'en')
        except Exception as mail_err:
            logger.warning(f"Courtesy email failed (non-blocking): {mail_err}")
        
        return jsonify({
            'message': 'Courtesy account generated successfully. The user will not hit the paywall.',
            'email': email,
            'temp_password': temp_pass,
            'distributor_id': distributor.id
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating courtesy account: {e}")
        return jsonify({'error': str(e)}), 500


# ──────────────────────────────────────────────
# ALL PLANS (Super Admin — including inactive)
# ──────────────────────────────────────────────


@billing_bp.route('/plans/all', methods=['GET'])
@jwt_required()
@admin_required
def get_all_plans():
    """Returns ALL plans (including inactive) for admin management."""
    try:
        db.session.rollback()
        plans = Plan.query.all()
        return jsonify([p.to_dict() for p in plans]), 200
    except Exception as e:
        logger.error(f"Error fetching all plans: {e}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# DISTRIBUTOR MANAGEMENT (Super Admin)
# ──────────────────────────────────────────────

@billing_bp.route('/distributors', methods=['GET'])
@jwt_required()
@admin_required
def get_all_distributors():
    """Returns all distributors along with their subscription/courtesy status."""
    try:
        db.session.rollback()
        distributors = Distributor.query.order_by(Distributor.created_at.desc()).all()
        # Ensure we return email from the associated user if available
        result = []
        for dist in distributors:
            data = dist.to_dict()
            # If the user model is attached, we can fetch email natively, or it's stored on dist
            # `dist.email` exists theoretically but user is the auth standard.
            user = User.query.filter_by(distributor_id=dist.id).first()
            if user:
                data['user_email'] = user.email
                data['user_name'] = user.name
            
            # Fetch plan name if applicable
            if dist.subscription_plan_id:
                plan = Plan.query.get(dist.subscription_plan_id)
                data['plan_name'] = plan.name if plan else None
            else:
                data['plan_name'] = None
                
            result.append(data)
            
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error fetching distributors: {e}")
        return jsonify({"error": str(e)}), 500


@billing_bp.route('/distributors/<int:distributor_id>/courtesy', methods=['PATCH'])
@jwt_required()
@admin_required
def toggle_courtesy_status(distributor_id):
    """Toggle the courtesy status of a distributor."""
    try:
        db.session.rollback()
        data = request.json
        is_courtesy = data.get('is_courtesy', False)
        
        distributor = Distributor.query.get(distributor_id)
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404
            
        distributor.is_courtesy = is_courtesy
        
        # If it's a courtesy account, they inherently have an active subscription
        # If toggled off, we shouldn't arbitrarily turn off their subscription if they
        # had actually paid, but for a strict paywall we assume courtesy is the override
        if is_courtesy:
            distributor.subscription_active = True
        else:
            # Only turn off if they don't have a valid plan (basic assumption, can be refined)
            # For simplicity, if courtesy is removed, they hit the paywall until dLocal confirms payment
            distributor.subscription_active = False 

        db.session.commit()
        return jsonify({
            'message': f"Courtesy status updated for {distributor.name}",
            'is_courtesy': distributor.is_courtesy,
            'subscription_active': distributor.subscription_active
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling courtesy status: {e}")
        return jsonify({"error": str(e)}), 500
