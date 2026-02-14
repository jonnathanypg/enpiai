"""
Contacts Routes - Unified Identity endpoint for aggregated contact history.
Combines Lead + Customer + Conversation + Appointment data into a single 360° view.

Migration Path: Identity aggregation will use DID-based profiles.
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.lead import Lead
from models.customer import Customer
from models.conversation import Conversation
from models.appointment import Appointment
from models.wellness_evaluation import WellnessEvaluation

logger = logging.getLogger(__name__)

contacts_bp = Blueprint('contacts', __name__)


def _get_distributor_id():
    """Get distributor_id from current JWT user."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    return user.distributor_id if user else None


@contacts_bp.route('/unified/<identifier>', methods=['GET'])
@jwt_required()
def get_unified_profile(identifier):
    """
    Get a 360° unified profile for a contact (Lead + Customer + Conversations + Appointments).

    Identifier can be:
    - Phone number (e.g., "593991234567")
    - Email address (e.g., "user@example.com")
    - Lead ID (e.g., "lead:42")
    - Customer ID (e.g., "customer:15")

    Returns aggregated data across all systems.
    """
    db.session.rollback()

    try:
        distributor_id = _get_distributor_id()
        if not distributor_id:
            return jsonify({'error': 'Unauthorized'}), 401

        lead = None
        customer = None

        # Resolve identifier
        if identifier.startswith('lead:'):
            lead_id = int(identifier.split(':')[1])
            lead = Lead.query.filter_by(id=lead_id, distributor_id=distributor_id).first()
        elif identifier.startswith('customer:'):
            customer_id = int(identifier.split(':')[1])
            customer = Customer.query.filter_by(id=customer_id, distributor_id=distributor_id).first()
        elif '@' in identifier:
            # Email lookup
            lead = Lead.query.filter_by(distributor_id=distributor_id, email=identifier).first()
            customer = Customer.query.filter_by(distributor_id=distributor_id, email=identifier).first()
        else:
            # Phone lookup
            phone_clean = identifier.replace('+', '').replace(' ', '').replace('-', '')
            lead = Lead.query.filter_by(distributor_id=distributor_id, phone=phone_clean).first()
            customer = Customer.query.filter_by(distributor_id=distributor_id, phone=phone_clean).first()

        if not lead and not customer:
            return jsonify({'error': 'Contact not found'}), 404

        # Build unified profile
        profile = {
            'identifier': identifier,
            'lead': None,
            'customer': None,
            'conversations': [],
            'appointments': [],
            'wellness_evaluations': [],
            'timeline': []
        }

        timeline = []

        # Lead data
        if lead:
            profile['lead'] = lead.to_dict()
            timeline.append({
                'type': 'lead_created',
                'date': lead.created_at.isoformat() if lead.created_at else None,
                'summary': f"Lead registered via {lead.source or 'unknown'}"
            })

            # Conversations for this lead
            conversations = Conversation.query.filter_by(
                distributor_id=distributor_id,
                lead_id=lead.id
            ).order_by(Conversation.created_at.desc()).limit(20).all()

            for conv in conversations:
                conv_data = {
                    'id': conv.id,
                    'channel': conv.channel.value if hasattr(conv.channel, 'value') else str(conv.channel),
                    'status': conv.status.value if hasattr(conv.status, 'value') else str(conv.status),
                    'created_at': conv.created_at.isoformat() if conv.created_at else None,
                    'last_message_at': conv.last_message_at.isoformat() if conv.last_message_at else None,
                    'message_count': conv.messages.count() if hasattr(conv.messages, 'count') else 0
                }
                profile['conversations'].append(conv_data)
                timeline.append({
                    'type': 'conversation',
                    'date': conv.created_at.isoformat() if conv.created_at else None,
                    'summary': f"Conversation via {conv_data['channel']} ({conv_data['status']})"
                })

            # Appointments for this lead
            appointments = Appointment.query.filter_by(
                distributor_id=distributor_id,
                lead_id=lead.id
            ).order_by(Appointment.scheduled_at.desc()).limit(10).all()

            for appt in appointments:
                profile['appointments'].append(appt.to_dict())
                timeline.append({
                    'type': 'appointment',
                    'date': appt.scheduled_at.isoformat() if appt.scheduled_at else None,
                    'summary': f"Appointment: {appt.title} ({appt.status.value})"
                })

        # Customer data
        if customer:
            profile['customer'] = customer.to_dict()
            timeline.append({
                'type': 'customer_created',
                'date': customer.created_at.isoformat() if customer.created_at else None,
                'summary': f"Converted to customer ({customer.customer_type})"
            })

            # Appointments for this customer
            appts = Appointment.query.filter_by(
                distributor_id=distributor_id,
                customer_id=customer.id
            ).order_by(Appointment.scheduled_at.desc()).limit(10).all()

            for appt in appts:
                if appt.to_dict() not in profile['appointments']:
                    profile['appointments'].append(appt.to_dict())
                    timeline.append({
                        'type': 'appointment',
                        'date': appt.scheduled_at.isoformat() if appt.scheduled_at else None,
                        'summary': f"Appointment: {appt.title} ({appt.status.value})"
                    })

            # Wellness evaluations
            evals = WellnessEvaluation.query.filter_by(
                distributor_id=distributor_id,
                customer_id=customer.id
            ).order_by(WellnessEvaluation.created_at.desc()).limit(5).all()

            for ev in evals:
                profile['wellness_evaluations'].append(ev.to_dict())
                timeline.append({
                    'type': 'wellness_evaluation',
                    'date': ev.created_at.isoformat() if ev.created_at else None,
                    'summary': f"Wellness eval — BMI: {ev.bmi}, Goal: {ev.primary_goal}"
                })

        # Sort timeline by date (most recent first)
        profile['timeline'] = sorted(
            [t for t in timeline if t.get('date')],
            key=lambda x: x['date'],
            reverse=True
        )

        return jsonify({'data': profile}), 200

    except Exception as e:
        logger.error(f"Unified profile error: {e}")
        return jsonify({'error': str(e)}), 500
