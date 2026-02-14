"""
Lead Routes - CRUD for prospect management, scoped to distributor.
Migration Path: Lead PII will be encrypted as sovereign blobs.
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.lead import Lead, LeadStatus, LeadSource, LeadType

logger = logging.getLogger(__name__)

leads_bp = Blueprint('leads', __name__)


def _get_distributor_id():
    """Get distributor_id from current JWT user"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    return user.distributor_id if user else None


@leads_bp.route('', methods=['GET'])
@jwt_required()
def list_leads():
    """List leads with optional filters (status, source, lead_type)"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        if not distributor_id:
            return jsonify({'error': 'Distributor not found'}), 404

        query = Lead.query.filter_by(distributor_id=distributor_id)

        # Filters
        status = request.args.get('status')
        if status:
            query = query.filter_by(status=status)

        source = request.args.get('source')
        if source:
            query = query.filter_by(source=source)

        lead_type = request.args.get('lead_type')
        if lead_type:
            query = query.filter_by(lead_type=lead_type)

        # Search by name or phone
        search = request.args.get('search')
        if search:
            query = query.filter(
                db.or_(
                    Lead.first_name.ilike(f'%{search}%'),
                    Lead.last_name.ilike(f'%{search}%'),
                    Lead.phone.ilike(f'%{search}%'),
                    Lead.email.ilike(f'%{search}%')
                )
            )

        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        pagination = query.order_by(Lead.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'data': [lead.to_dict() for lead in pagination.items],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200

    except Exception as e:
        logger.error(f"List leads error: {e}")
        return jsonify({'error': str(e)}), 500


@leads_bp.route('', methods=['POST'])
@jwt_required()
def create_lead():
    """Create a new lead"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        if not distributor_id:
            return jsonify({'error': 'Distributor not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        lead = Lead(
            distributor_id=distributor_id,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            phone=data.get('phone'),
            country=data.get('country'),
            city=data.get('city'),
            source=data.get('source', LeadSource.MANUAL.value),
            lead_type=data.get('lead_type', LeadType.UNKNOWN.value),
            notes=data.get('notes'),
            tags=data.get('tags', []),
        )
        db.session.add(lead)
        db.session.commit()

        logger.info(f"Lead created: {lead.full_name} for distributor {distributor_id}")
        return jsonify({'data': lead.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Create lead error: {e}")
        return jsonify({'error': str(e)}), 500


@leads_bp.route('/<int:lead_id>', methods=['GET'])
@jwt_required()
def get_lead(lead_id):
    """Get a single lead"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        lead = Lead.query.filter_by(id=lead_id, distributor_id=distributor_id).first()
        if not lead:
            return jsonify({'error': 'Lead not found'}), 404

        return jsonify({'data': lead.to_dict()}), 200

    except Exception as e:
        logger.error(f"Get lead error: {e}")
        return jsonify({'error': str(e)}), 500


@leads_bp.route('/<int:lead_id>', methods=['PUT'])
@jwt_required()
def update_lead(lead_id):
    """Update a lead"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        lead = Lead.query.filter_by(id=lead_id, distributor_id=distributor_id).first()
        if not lead:
            return jsonify({'error': 'Lead not found'}), 404

        data = request.get_json()
        updatable = [
            'first_name', 'last_name', 'email', 'phone',
            'country', 'city', 'status', 'source', 'lead_type',
            'notes', 'tags'
        ]

        for field in updatable:
            if field in data:
                setattr(lead, field, data[field])

        db.session.commit()
        return jsonify({'data': lead.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update lead error: {e}")
        return jsonify({'error': str(e)}), 500


@leads_bp.route('/<int:lead_id>', methods=['DELETE'])
@jwt_required()
def delete_lead(lead_id):
    """Delete a lead"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        lead = Lead.query.filter_by(id=lead_id, distributor_id=distributor_id).first()
        if not lead:
            return jsonify({'error': 'Lead not found'}), 404

        db.session.delete(lead)
        db.session.commit()

        logger.info(f"Lead {lead_id} deleted for distributor {distributor_id}")
        return jsonify({'data': {'message': 'Lead deleted successfully'}}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete lead error: {e}")
        return jsonify({'error': str(e)}), 500


@leads_bp.route('/<int:lead_id>/qualify', methods=['POST'])
@jwt_required()
def qualify_lead(lead_id):
    """Update lead qualification (status and lead_type)"""
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        lead = Lead.query.filter_by(id=lead_id, distributor_id=distributor_id).first()
        if not lead:
            return jsonify({'error': 'Lead not found'}), 404

        data = request.get_json()
        if 'status' in data:
            lead.status = data['status']
        if 'lead_type' in data:
            lead.lead_type = data['lead_type']
        if 'notes' in data:
            lead.notes = data['notes']

        db.session.commit()

        logger.info(f"Lead {lead_id} qualified: {lead.status} / {lead.lead_type}")
        return jsonify({'data': lead.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Qualify lead error: {e}")
        return jsonify({'error': str(e)}), 500
