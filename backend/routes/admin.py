"""
Admin Routes - Super Admin endpoints for platform management.
Controls global config, subscription plans, tenant oversight, and global RAG.

Migration Path: Admin governance will be decentralized via DAO voting.
"""
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from decorators import super_admin_required
from models.platform_config import PlatformConfig
from models.subscription import Plan, Subscription, SubscriptionStatus, PlanInterval
from models.distributor import Distributor
from models.user import User, UserRole
from models.lead import Lead
from models.customer import Customer
from models.conversation import Conversation, Message

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


# =========================================================================
# Global Platform Config
# =========================================================================

@admin_bp.route('/config', methods=['GET'])
@jwt_required()
@super_admin_required
def get_platform_config():
    """Get global platform configuration."""
    db.session.rollback()
    try:
        config = PlatformConfig.get_config()
        return jsonify({'data': config.to_dict()}), 200
    except Exception as e:
        logger.error(f"Get config error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/config', methods=['PUT'])
@jwt_required()
@super_admin_required
def update_platform_config():
    """Update global platform configuration (failover toggle, RAG, limits)."""
    db.session.rollback()
    try:
        config = PlatformConfig.get_config()
        data = request.get_json()

        updatable = [
            'enable_failover', 'default_llm_provider', 'default_llm_model',
            'global_rag_enabled', 'global_rag_namespace',
            'maintenance_mode', 'max_agents_per_distributor',
            'max_documents_per_distributor'
        ]

        for field in updatable:
            if field in data:
                setattr(config, field, data[field])

        user_id = get_jwt_identity()
        config.updated_by = int(user_id)

        db.session.commit()
        logger.info(f"Platform config updated by user {user_id}")
        return jsonify({'data': config.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update config error: {e}")
        return jsonify({'error': str(e)}), 500


# =========================================================================
# Subscription Plans (CRUD)
# =========================================================================

@admin_bp.route('/plans', methods=['GET'])
@jwt_required()
@super_admin_required
def list_plans():
    """List all subscription plans."""
    db.session.rollback()
    try:
        plans = Plan.query.order_by(Plan.price_monthly.asc()).all()
        return jsonify({'data': [p.to_dict() for p in plans]}), 200
    except Exception as e:
        logger.error(f"List plans error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/plans', methods=['POST'])
@jwt_required()
@super_admin_required
def create_plan():
    """Create a new subscription plan."""
    db.session.rollback()
    try:
        data = request.get_json()
        if not data or not data.get('name'):
            return jsonify({'error': 'Plan name is required'}), 400

        plan = Plan(
            name=data['name'],
            description=data.get('description'),
            price_monthly=data.get('price_monthly', 0.0),
            price_annual=data.get('price_annual', 0.0),
            currency=data.get('currency', 'USD'),
            features=data.get('features'),
            is_active=data.get('is_active', True),
            is_default=data.get('is_default', False),
        )
        db.session.add(plan)
        db.session.commit()

        logger.info(f"Plan created: {plan.name}")
        return jsonify({'data': plan.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Create plan error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/plans/<int:plan_id>', methods=['PUT'])
@jwt_required()
@super_admin_required
def update_plan(plan_id):
    """Update a subscription plan."""
    db.session.rollback()
    try:
        plan = Plan.query.get(plan_id)
        if not plan:
            return jsonify({'error': 'Plan not found'}), 404

        data = request.get_json()
        updatable = ['name', 'description', 'price_monthly', 'price_annual',
                      'currency', 'features', 'is_active', 'is_default']

        for field in updatable:
            if field in data:
                setattr(plan, field, data[field])

        db.session.commit()
        return jsonify({'data': plan.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update plan error: {e}")
        return jsonify({'error': str(e)}), 500


# =========================================================================
# Tenant (Distributor) Management
# =========================================================================

@admin_bp.route('/tenants', methods=['GET'])
@jwt_required()
@super_admin_required
def list_tenants():
    """List all distributors with their subscription status."""
    db.session.rollback()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        pagination = Distributor.query.order_by(
            Distributor.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        tenants = []
        for dist in pagination.items:
            tenant_data = dist.to_dict()
            sub = Subscription.query.filter_by(distributor_id=dist.id).first()
            tenant_data['subscription'] = sub.to_dict() if sub else None
            tenants.append(tenant_data)

        return jsonify({
            'data': tenants,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
            }
        }), 200

    except Exception as e:
        logger.error(f"List tenants error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/tenants/<int:distributor_id>/subscription', methods=['POST'])
@jwt_required()
@super_admin_required
def assign_subscription(distributor_id):
    """Assign or update a subscription for a distributor."""
    db.session.rollback()
    try:
        distributor = Distributor.query.get(distributor_id)
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        data = request.get_json()
        plan_id = data.get('plan_id')
        if not plan_id:
            return jsonify({'error': 'plan_id is required'}), 400

        plan = Plan.query.get(plan_id)
        if not plan:
            return jsonify({'error': 'Plan not found'}), 404

        # Deactivate existing subscription
        existing = Subscription.query.filter_by(distributor_id=distributor_id).first()
        if existing:
            existing.status = SubscriptionStatus.CANCELLED
            existing.cancelled_at = datetime.utcnow()

        # Create new subscription
        status = data.get('status', SubscriptionStatus.ACTIVE.value)
        sub = Subscription(
            distributor_id=distributor_id,
            plan_id=plan_id,
            interval=data.get('interval', PlanInterval.MONTHLY.value),
            status=status,
            notes=data.get('notes'),
        )

        # If courtesy, set status accordingly
        if data.get('is_courtesy'):
            sub.status = SubscriptionStatus.COURTESY

        db.session.add(sub)
        db.session.commit()

        logger.info(f"Subscription assigned to distributor {distributor_id}: Plan {plan.name}")
        return jsonify({'data': sub.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Assign subscription error: {e}")
        return jsonify({'error': str(e)}), 500


# =========================================================================
# Global RAG Management
# =========================================================================

@admin_bp.route('/rag/upload', methods=['POST'])
@jwt_required()
@super_admin_required
def upload_global_rag():
    """Upload a document to the global RAG namespace (Herbalife knowledge base)."""
    db.session.rollback()
    try:
        data = request.get_json()
        if not data or not data.get('chunks'):
            return jsonify({'error': 'Text chunks required'}), 400

        from services.rag_service import rag_service

        document_id = data.get('document_id', f"global_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
        metadata = data.get('metadata', {})
        metadata['source'] = 'super_admin'
        metadata['scope'] = 'global'

        vector_ids = rag_service.upsert_document(
            text_chunks=data['chunks'],
            distributor_id='global',  # Special namespace
            document_id=document_id,
            metadata=metadata
        )

        return jsonify({
            'data': {
                'document_id': document_id,
                'chunks_indexed': len(vector_ids),
            }
        }), 201

    except Exception as e:
        logger.error(f"Global RAG upload error: {e}")
        return jsonify({'error': str(e)}), 500


# =========================================================================
# Platform Metrics (Dashboard Data)
# =========================================================================

@admin_bp.route('/metrics', methods=['GET'])
@jwt_required()
@super_admin_required
def get_platform_metrics():
    """Get platform-wide metrics for the Super Admin dashboard."""
    db.session.rollback()
    try:
        total_distributors = Distributor.query.count()
        active_subscriptions = Subscription.query.filter(
            Subscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIAL,
                SubscriptionStatus.COURTESY
            ])
        ).count()
        total_leads = Lead.query.count()
        total_customers = Customer.query.count()
        total_conversations = Conversation.query.count()
        total_messages = Message.query.count()

        # Monthly Recurring Revenue (MRR) estimate
        active_monthly = db.session.query(
            db.func.sum(Plan.price_monthly)
        ).join(Subscription).filter(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.interval == PlanInterval.MONTHLY
        ).scalar() or 0.0

        active_annual = db.session.query(
            db.func.sum(Plan.price_annual)
        ).join(Subscription).filter(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.interval == PlanInterval.ANNUAL
        ).scalar() or 0.0

        mrr = active_monthly + (active_annual / 12.0)

        return jsonify({
            'data': {
                'total_distributors': total_distributors,
                'active_subscriptions': active_subscriptions,
                'total_leads': total_leads,
                'total_customers': total_customers,
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'mrr': round(mrr, 2),
            }
        }), 200

    except Exception as e:
        logger.error(f"Platform metrics error: {e}")
        return jsonify({'error': str(e)}), 500
