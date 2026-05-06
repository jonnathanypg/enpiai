"""
Payment Routes - Subscription management and checkout.
Handles the "Pre-login Subscription" flow where a user registers and pays in one step.
Migration Path: Payment logic moves to smart contracts/crypto in the future.
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token
from extensions import db
from models.user import User, UserRole
from models.distributor import Distributor, SubscriptionTier
from models.subscription import Subscription, Plan, PlanInterval, SubscriptionStatus
from models.transaction import Transaction, TransactionStatus, TransactionType
from services.rebill_service import RebillService


logger = logging.getLogger(__name__)

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/plans', methods=['GET'])
def list_plans():
    """List public subscription plans."""
    plans = Plan.query.filter_by(is_active=True).all()
    if not plans:
        # Seed default plans if none exist (for development convenience)
        seed_plans()
        plans = Plan.query.filter_by(is_active=True).all()
        
    return jsonify({'data': [p.to_dict() for p in plans]}), 200

@payments_bp.route('/subscribe', methods=['POST'])
def subscribe():
    """
    Public endpoint: Register User + Distributor + Subscription.
    Payload: {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "secret_password",
        "business_name": "John's Club",
        "plan_id": 1,
        "interval": "monthly"
    }
    """
    db.session.rollback()
    try:
        data = request.get_json()
        
        # 1. Validation
        required = ['name', 'email', 'password', 'plan_id']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400

        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409

        plan = Plan.query.get(data['plan_id'])
        if not plan:
            return jsonify({'error': 'Invalid plan'}), 400

        # 2. Create Distributor
        distributor = Distributor(
            name=data['name'],
            business_name=data.get('business_name'),
            subscription_tier=SubscriptionTier.PROFESSIONAL, # Default to paid
            country=data.get('country', 'Ecuador')
        )
        db.session.add(distributor)
        db.session.flush() # Get ID

        # 3. Create User
        user = User(
            email=data['email'],
            name=data['name'],
            role=UserRole.ADMIN, # Default for new signup
            distributor_id=distributor.id
        )
        user.set_password(data['password'])
        db.session.add(user)

        # 4. Create Subscription (Mock Payment Success)
        interval = PlanInterval.ANNUAL if data.get('interval') == 'annual' else PlanInterval.MONTHLY
        
        # Calculate expiry
        now = datetime.utcnow()
        if interval == PlanInterval.ANNUAL:
            end_date = now + timedelta(days=365)
            next_payment = end_date
        else:
            end_date = now + timedelta(days=30)
            next_payment = end_date

        subscription = Subscription(
            distributor_id=distributor.id,
            plan_id=plan.id,
            interval=interval,
            status=SubscriptionStatus.PENDING, # Initially pending checkout
            start_date=now,
            notes='Pre-login subscription via /subscribe'
        )
        db.session.add(subscription)
        
        # 5. Integrate with Rebill (Payment Link Flow)
        checkout_url = None
        try:
            rebill = RebillService()
            # We create a specific payment link for this user/plan
            # This allows us to pass metadata (user_id) for the webhook
            link_data = rebill.get_payment_link_for_plan(
                plan_id=plan.rebill_plan_id,
                user_email=user.email,
                user_id=user.id,
                user_name=user.name,
                plan_name=plan.name
            )
            checkout_url = link_data.get('url')
            
            # We don't set rebill_subscription_id yet; the webhook will do that
            subscription.rebill_subscription_id = "pending_link_" + link_data.get('id', '')
            
        except Exception as rebill_err:
            logger.error(f"Rebill Payment Link creation failed: {rebill_err}")
            # Fallback or error? For now, we log but return success so user is created
            # In produciton, maybe return 500 if payment is mandatory immediately

        db.session.commit()

        # 6. Auto-Login
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        logger.info(f"New subscription registered: {user.email} for plan {plan.name}")

        return jsonify({
            'message': 'Subscription initiated',
            'checkoutUrl': checkout_url,
            'data': {
                'user': user.to_dict(),
                'distributor': distributor.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Subscription error: {e}")
        return jsonify({'error': str(e)}), 500

def seed_plans():
    """Helper to seed plans if missing."""
    starter = Plan(
        name='Starter',
        description='Perfect for new distributors.',
        price_monthly=29.00,
        price_annual=290.00,
        features={'max_agents': 1, 'channels': ['whatsapp']},
        is_default=True,
        rebill_plan_id='test_pln_44de287e76084ddb9442fcf5dd928c87'
    )
    pro = Plan(
        name='Professional',
        description='Scaling your business.',
        price_monthly=59.00,
        price_annual=590.00,
        features={'max_agents': 3, 'channels': ['whatsapp', 'telegram', 'email']},
        is_default=False,
        rebill_plan_id='test_pln_2b67bc9b65d640fdae6785d89a393344'
    )
    elite = Plan(
        name='Enterprise',
        description='Full automation for large clusters.',
        price_monthly=99.00,
        price_annual=990.00,
        features={'max_agents': 10, 'channels': ['whatsapp', 'telegram', 'email', 'google']},
        is_default=False,
        rebill_plan_id='test_pln_c8cdf6ef9f044fc5aa7aba1c935e0d91'
    )
    db.session.add(starter)
    db.session.add(pro)
    db.session.add(elite)
    db.session.commit()

@payments_bp.route('/webhook/rebill', methods=['POST'])
def rebill_webhook():
    """
    Handle Rebill webhook events.
    Documentation: Based on Rebill v3 Payments object structure.
    """
    try:
        # Prevent "MySQL has gone away"
        db.session.rollback()
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data'}), 400

        # Based on Rebill v3 docs, the payload might be the payment object or wrapped.
        # We'll handle 'payment.approved' event or just look for status.
        payment_data = data.get('payment', data)
        status = payment_data.get('status')
        metadata = payment_data.get('metadata', {})
        user_id = metadata.get('user_id')
        email = metadata.get('email') or (payment_data.get('customer', {}) if isinstance(payment_data.get('customer'), dict) else {}).get('email')
        
        logger.info(f"Rebill Webhook: Status={status}, User={user_id}, Email={email}")

        if status == 'approved':
            # 1. Resolve User
            user = None
            if user_id:
                user = User.query.get(user_id)
            elif email:
                user = User.query.filter_by(email=email).first()

            if user and user.distributor_id:
                # 2. Find the pending subscription
                sub = Subscription.query.filter_by(
                    distributor_id=user.distributor_id,
                    status=SubscriptionStatus.PENDING
                ).order_by(Subscription.created_at.desc()).first()
                
                if sub:
                    sub.status = SubscriptionStatus.ACTIVE
                    sub.last_payment_at = datetime.utcnow()
                    
                    # Store Rebill's IDs
                    sub.rebill_subscription_id = payment_data.get('subscriptionId')
                    
                    # Set expiry/next payment based on interval
                    if sub.interval == PlanInterval.MONTHLY:
                        sub.end_date = datetime.utcnow() + timedelta(days=32)
                        sub.next_payment_at = datetime.utcnow() + timedelta(days=30)
                    else:
                        sub.end_date = datetime.utcnow() + timedelta(days=370)
                        sub.next_payment_at = datetime.utcnow() + timedelta(days=365)
                        
                    db.session.add(sub) # Ensure session tracks it

                    # 3. Log Transaction
                    amount = float(payment_data.get('amount', {}).get('value', 0)) if isinstance(payment_data.get('amount'), dict) else float(payment_data.get('amount', 0))
                    currency = payment_data.get('currency', 'USD') # Default or extract

                    transaction = Transaction(
                        distributor_id=user.distributor_id,
                        rebill_id=payment_data.get('id'),
                        amount=amount,
                        currency=currency,
                        status=TransactionStatus.APPROVED,
                        type=TransactionType.PAYMENT,
                        description=f"Subscription Payment for {sub.plan.name}",
                        created_at=datetime.utcnow()
                    )
                    db.session.add(transaction)
                    
                    db.session.commit()
                    logger.info(f"Subscription {sub.id} ACTIVATED and Transaction {transaction.id} logged for Distributor {user.distributor_id}")
                else:
                    logger.info(f"No pending subscription found for user {user.id}")
            else:
                logger.warning(f"Could not resolve user/distributor for webhook data")

        return jsonify({'status': 'received'}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Rebill Webhook Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
