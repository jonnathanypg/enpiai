"""
Wellness Evaluation Routes - Submit and view wellness evaluations.
The POST /evaluate endpoint is PUBLIC (no auth) so prospects can fill it from a shared link.
Migration Path: Health data is PII — encrypted as sovereign blobs.
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.wellness_evaluation import WellnessEvaluation
from models.lead import Lead, LeadSource

logger = logging.getLogger(__name__)

wellness_bp = Blueprint('wellness', __name__)


@wellness_bp.route('/evaluate/<string:distributor_ref>', methods=['POST'])
def submit_evaluation(distributor_ref):
    """Submit a wellness evaluation — PUBLIC endpoint (no auth).
    Prospects access this via a personalized link from the distributor (herbalife_id or db id).
    Creates a lead automatically if one doesn't exist.
    """
    db.session.rollback()

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Lookup distributor by herbalife_id or db id
        from models.distributor import Distributor
        distributor = None
        if distributor_ref.isdigit():
            distributor = Distributor.query.get(int(distributor_ref))
        if not distributor:
            distributor = Distributor.query.filter_by(herbalife_id=distributor_ref).first()
            
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404
            
        distributor_id = distributor.id

        # Try to find or create a lead for this prospect
        lead_id = data.get('lead_id')
        lead = None

        if not lead_id:
            # Auto-create a lead from the evaluation data
            phone = data.get('phone')
            email = data.get('email')

            if phone:
                lead = Lead.query.filter_by(
                    distributor_id=distributor_id, phone=phone
                ).first()
            if not lead and email:
                lead = Lead.query.filter_by(
                    distributor_id=distributor_id, email=email
                ).first()

            if not lead:
                lead = Lead(
                    distributor_id=distributor_id,
                    first_name=data.get('first_name'),
                    last_name=data.get('last_name'),
                    email=email,
                    phone=phone,
                    source=LeadSource.WEB_FORM,
                )
                db.session.add(lead)
                db.session.flush()

            lead_id = lead.id

        # Create the evaluation
        evaluation = WellnessEvaluation(
            distributor_id=distributor_id,
            lead_id=lead_id,
            customer_id=data.get('customer_id'),
            age=data.get('age'),
            gender=data.get('gender'),
            height_cm=data.get('height_cm'),
            weight_kg=data.get('weight_kg'),
            health_conditions=data.get('health_conditions', []),
            medications=data.get('medications'),
            allergies=data.get('allergies', []),
            activity_level=data.get('activity_level'),
            exercise_frequency=data.get('exercise_frequency'),
            meals_per_day=data.get('meals_per_day'),
            water_intake_liters=data.get('water_intake_liters'),
            diet_description=data.get('diet_description'),
            primary_goal=data.get('primary_goal'),
            target_weight_kg=data.get('target_weight_kg'),
            motivation=data.get('motivation'),
            sleep_hours=data.get('sleep_hours'),
            sleep_quality=data.get('sleep_quality'),
            source=data.get('source', 'web_form'),
        )

        # Auto-calculate BMI
        evaluation.calculate_bmi()

        db.session.add(evaluation)
        db.session.commit()

        logger.info(f"Wellness evaluation submitted for distributor {distributor_id}, lead {lead_id}")

        return jsonify({'data': evaluation.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Submit evaluation error: {e}")
        return jsonify({'error': str(e)}), 500


@wellness_bp.route('/evaluations', methods=['GET'])
@jwt_required()
def list_evaluations():
    """List all wellness evaluations for the authenticated distributor"""
    db.session.rollback()

    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user or not user.distributor_id:
            return jsonify({'error': 'Distributor not found'}), 404

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        pagination = WellnessEvaluation.query.filter_by(
            distributor_id=user.distributor_id
        ).order_by(
            WellnessEvaluation.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'data': [e.to_dict() for e in pagination.items],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200

    except Exception as e:
        logger.error(f"List evaluations error: {e}")
        return jsonify({'error': str(e)}), 500


@wellness_bp.route('/evaluations/<int:eval_id>', methods=['GET'])
@jwt_required()
def get_evaluation(eval_id):
    """Get a single wellness evaluation"""
    db.session.rollback()

    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user or not user.distributor_id:
            return jsonify({'error': 'Distributor not found'}), 404

        evaluation = WellnessEvaluation.query.filter_by(
            id=eval_id, distributor_id=user.distributor_id
        ).first()

        if not evaluation:
            return jsonify({'error': 'Evaluation not found'}), 404

        return jsonify({'data': evaluation.to_dict()}), 200

    except Exception as e:
        logger.error(f"Get evaluation error: {e}")
        return jsonify({'error': str(e)}), 500


@wellness_bp.route('/evaluations/<int:eval_id>/pdf', methods=['POST'])
@jwt_required()
def generate_pdf(eval_id):
    """Trigger PDF generation for an evaluation"""
    db.session.rollback()

    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user or not user.distributor_id:
            return jsonify({'error': 'Distributor not found'}), 404

        evaluation = WellnessEvaluation.query.filter_by(
            id=eval_id, distributor_id=user.distributor_id
        ).first()

        if not evaluation:
            return jsonify({'error': 'Evaluation not found'}), 404

        # Trigger async PDF generation
        from services.pdf_service import pdf_service
        # We pass the distributor object, so we need to fetch it or rely on lazy load if session active
        # But pdf_service expects model instance.
        from models.distributor import Distributor
        distributor = Distributor.query.get(user.distributor_id)
        
        # Dispatch
        # verify if we want async or sync. Let's try async if available, else sync.
        # The service handles the fallback.
        pdf_service.generate_wellness_report_async(evaluation, distributor)

        return jsonify({'message': 'PDF generation started', 'status': 'processing'}), 202

    except Exception as e:
        logger.error(f"Generate PDF error: {e}")
        return jsonify({'error': str(e)}), 500
