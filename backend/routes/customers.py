"""
Customer Routes - CRUD for customer management, scoped to distributor.
Migration Path: Customer PII encrypted as sovereign blobs.
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.customer import Customer

logger = logging.getLogger(__name__)

customers_bp = Blueprint('customers', __name__)


def _get_distributor_id():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    return user.distributor_id if user else None


@customers_bp.route('', methods=['GET'])
@jwt_required()
def list_customers():
    """List customers with optional search"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        if not distributor_id:
            return jsonify({'error': 'Distributor not found'}), 404

        query = Customer.query.filter_by(distributor_id=distributor_id)

        search = request.args.get('search')
        if search:
            query = query.filter(
                db.or_(
                    Customer.first_name.ilike(f'%{search}%'),
                    Customer.last_name.ilike(f'%{search}%'),
                    Customer.phone.ilike(f'%{search}%'),
                    Customer.email.ilike(f'%{search}%')
                )
            )

        customer_type = request.args.get('customer_type')
        if customer_type:
            query = query.filter_by(customer_type=customer_type)

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        pagination = query.order_by(Customer.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'data': [c.to_dict() for c in pagination.items],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200

    except Exception as e:
        logger.error(f"List customers error: {e}")
        return jsonify({'error': str(e)}), 500


@customers_bp.route('', methods=['POST'])
@jwt_required()
def create_customer():
    """Create a new customer"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        if not distributor_id:
            return jsonify({'error': 'Distributor not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        customer = Customer(
            distributor_id=distributor_id,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            phone=data.get('phone'),
            country=data.get('country'),
            city=data.get('city'),
            ident_number=data.get('ident_number'),
            customer_type=data.get('customer_type', 'retail'),
            original_lead_id=data.get('original_lead_id'),
            customer_metadata=data.get('metadata'),
        )
        db.session.add(customer)
        db.session.commit()

        logger.info(f"Customer created: {customer.full_name}")
        return jsonify({'data': customer.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Create customer error: {e}")
        return jsonify({'error': str(e)}), 500


@customers_bp.route('/<int:customer_id>', methods=['GET'])
@jwt_required()
def get_customer(customer_id):
    """Get a single customer"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        customer = Customer.query.filter_by(id=customer_id, distributor_id=distributor_id).first()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        return jsonify({'data': customer.to_dict()}), 200

    except Exception as e:
        logger.error(f"Get customer error: {e}")
        return jsonify({'error': str(e)}), 500


@customers_bp.route('/<int:customer_id>', methods=['PUT'])
@jwt_required()
def update_customer(customer_id):
    """Update a customer"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        customer = Customer.query.filter_by(id=customer_id, distributor_id=distributor_id).first()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        data = request.get_json()
        updatable = [
            'first_name', 'last_name', 'email', 'phone',
            'country', 'city', 'ident_number', 'customer_type'
        ]

        for field in updatable:
            if field in data:
                setattr(customer, field, data[field])

        if 'metadata' in data:
            customer.customer_metadata = data['metadata']

        db.session.commit()
        return jsonify({'data': customer.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update customer error: {e}")
        return jsonify({'error': str(e)}), 500


@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
@jwt_required()
def delete_customer(customer_id):
    """Delete a customer"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        customer = Customer.query.filter_by(id=customer_id, distributor_id=distributor_id).first()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        db.session.delete(customer)
        db.session.commit()

        return jsonify({'data': {'message': 'Customer deleted successfully'}}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete customer error: {e}")
        return jsonify({'error': str(e)}), 500
