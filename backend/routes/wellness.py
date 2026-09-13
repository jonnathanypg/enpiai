"""
Wellness Evaluation Routes - Submit and view wellness evaluations.
The POST /evaluate endpoint is PUBLIC (no auth) so prospects can fill it from a shared link.
Migration Path: Health data is PII — encrypted as sovereign blobs.
"""
import logging
import os
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.wellness_evaluation import WellnessEvaluation
from models.lead import Lead, LeadSource
from services.email_service import email_service
from services.pdf_service import pdf_service
from services.messaging_service import messaging_service

logger = logging.getLogger(__name__)

wellness_bp = Blueprint('wellness', __name__)


@wellness_bp.route('/evaluate/<string:distributor_ref>', methods=['POST'])
def submit_evaluation(distributor_ref):
    """Submit a wellness evaluation — PUBLIC endpoint (no auth).
    Prospects access this via a personalized link from the distributor (herbalife_id or db id).
    Creates a lead automatically if one doesn't exist.
    Generates an AI-powered diagnosis and recommendations.
    """
    db.session.rollback()

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Lookup distributor by herbalife_id (priority) or db id (fallback)
        from models.distributor import Distributor
        distributor = Distributor.query.filter_by(herbalife_id=distributor_ref).first()
        
        if not distributor and distributor_ref.isdigit():
            distributor = Distributor.query.get(int(distributor_ref))
            
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
                phone_h = Lead.generate_hash(phone)
                lead = Lead.query.filter_by(
                    distributor_id=distributor_id, phone_hash=phone_h
                ).first()
            if not lead and email:
                email_h = Lead.generate_hash(email)
                lead = Lead.query.filter_by(
                    distributor_id=distributor_id, email_hash=email_h
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
            blood_pressure=data.get('blood_pressure'),
            pulse=data.get('pulse'),
            energy_level=data.get('energy_level'),
            symptoms=data.get('symptoms', []),
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
            observations=data.get('observations'),
            language=data.get('language', distributor.language or 'es'),
            source=data.get('source', 'web_form'),
        )

        # Auto-calculate BMI
        evaluation.calculate_bmi()

        # Generate AI Diagnosis immediately so the user never hangs or waits 10 minutes
        try:
            from services.ai_diagnostic_service import AIDiagnosticService
            diag_result = AIDiagnosticService.generate_diagnosis(evaluation=evaluation, distributor=distributor)
            evaluation.diagnosis = diag_result.get('diagnosis')
            evaluation.recommendations = diag_result.get('recommendations')
            evaluation.recommended_products = diag_result.get('recommended_products')
        except Exception as diag_err:
            logger.error(f"Immediate diagnosis generation error: {diag_err}")

        # Save evaluation data
        db.session.add(evaluation)
        db.session.commit()
        logger.info(f"Wellness evaluation saved with diagnosis: {evaluation.id}")

        # --- Trigger Background Processing (PDF + Messaging) ---
        try:
            from tasks import process_wellness_evaluation
            process_wellness_evaluation.delay(evaluation.id, distributor.id, data)
            logger.info(f"Background task triggered for evaluation {evaluation.id}")
        except Exception as task_err:
            logger.warning(f"Background task dispatch (Celery) skipped/failed: {task_err}")
            # Try instant PDF generation fallback
            try:
                from services.pdf_service import pdf_service
                pdf_path = pdf_service.generate_wellness_report(evaluation, distributor)
                if pdf_path:
                    evaluation.pdf_report_path = pdf_path
                    db.session.commit()
            except Exception as pdf_err:
                logger.debug(f"Direct PDF generation fallback error: {pdf_err}")

        result = evaluation.to_dict()
        # Inject contact info and distributor info from request data for immediate display
        result['first_name'] = data.get('first_name') or result.get('first_name')
        result['email'] = data.get('email') or result.get('email')
        result['contact_name'] = result['first_name']
        result['distributor_name'] = distributor.name
        result['distributor_herbalife_id'] = distributor.herbalife_id or str(distributor.id)

        return jsonify({'data': result}), 201

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


@wellness_bp.route('/evaluations/<int:eval_id>', methods=['DELETE'])
@jwt_required()
def delete_evaluation(eval_id):
    """Delete a wellness evaluation"""
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

        db.session.delete(evaluation)
        db.session.commit()

        logger.info(f"Evaluation {eval_id} deleted by user {user_id}")
        return jsonify({'message': 'Evaluation deleted'}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete evaluation error: {e}")
        return jsonify({'error': str(e)}), 500
@wellness_bp.route('/evaluate/results/<int:eval_id>', methods=['GET'])
def get_public_evaluation(eval_id):
    """Public route for prospects to fetch their evaluation results (polling)"""
    db.session.rollback()
    try:
        evaluation = WellnessEvaluation.query.get(eval_id)
        if not evaluation:
            return jsonify({'error': 'Evaluation not found'}), 404
            
        # Return only what's needed for the results display
        result = evaluation.to_dict()
        
        # Add PDF URL if available
        if evaluation.pdf_report_path:
            api_base = current_app.config.get('API_BASE_URL', 'http://localhost:5000')
            result['pdf_url'] = f"{api_base}/api/wellness/reports/{evaluation.pdf_report_path}"
            
        return jsonify({'data': result}), 200
    except Exception as e:
        logger.error(f"Get public evaluation error: {e}")
        return jsonify({'error': str(e)}), 500


@wellness_bp.route('/reports/<filename>', methods=['GET'])
def get_report(filename):
    """Serve a wellness report PDF"""
    try:
        # Use absolute path for safety
        upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads'))
        report_folder = os.path.join(upload_folder, 'reports')
        return send_from_directory(report_folder, filename)
    except Exception as e:
        logger.error(f"Error serving report {filename}: {e}")
        return jsonify({'error': 'Report not found or error serving file'}), 404
