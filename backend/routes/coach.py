"""
Coach Routes - Management of Coach Mode settings, tasks checklist, and AI Coach advice.
"""
import logging
from datetime import datetime, timedelta
import pytz
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.distributor import Distributor
from services.ai_coach_service import ai_coach_service, TASK_METADATA
from services.messaging_service import messaging_service
from services.cron_service import CronService

logger = logging.getLogger(__name__)

coach_bp = Blueprint('coach', __name__)

def _get_current_distributor():
    """Helper: get the distributor associated with the current JWT user"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user or not user.distributor_id:
        return None, None
    distributor = Distributor.query.get(user.distributor_id)
    return user, distributor

@coach_bp.route('/roadmap', methods=['GET'])
@jwt_required()
def get_roadmap():
    """Get coach roadmap progress and today's tasks checklist"""
    db.session.rollback()

    try:
        user, distributor = _get_current_distributor()
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        level = distributor.herbalife_level or "Distribuidor Independiente"
        meta = ai_coach_service.get_level_metadata(level)
        
        # Check if tasks are initialized
        tasks_status = distributor.coach_daily_tasks_status
        if not tasks_status:
            tasks_status = ai_coach_service.generate_daily_tasks_checklist(level)
            distributor.coach_daily_tasks_status = tasks_status
            db.session.commit()

        # Format challenges for UI
        lang = distributor.language or 'es'
        lang_key = 'es' if lang == 'es' else 'en'
        
        daily_challenges = []
        for task_id, is_completed in tasks_status.items():
            daily_challenges.append({
                'id': task_id,
                'label': TASK_METADATA.get(task_id, {}).get(lang_key, task_id),
                'is_completed': is_completed
            })

        # Static / dynamic weekly and monthly goals based on level
        weekly_goals = []
        monthly_goals = []
        
        if level in ["Distribuidor Independiente", "Consultor Mayor", "Constructor del Éxito", "Productor Calificado"]:
            weekly_goals = [
                {"id": "wk_wellness_3", "label": "Completar 3 Evaluaciones de Bienestar", "is_completed": False},
                {"id": "wk_talk_25", "label": "Hablar con 25 personas acumuladas", "is_completed": False}
            ]
            monthly_goals = [
                {"id": "mo_volume_500", "label": "Registrar 500 Puntos de Volumen personal", "is_completed": False},
                {"id": "mo_sponsor_1", "label": "Patrocinar a 1 nuevo miembro en el equipo", "is_completed": False}
            ]
        else: # Supervisor and higher
            weekly_goals = [
                {"id": "wk_wellness_10", "label": "Completar 10 Evaluaciones de Bienestar", "is_completed": False},
                {"id": "wk_dist_meeting", "label": "Hacer 1 reunión de capacitación con tus Distribuidores", "is_completed": False}
            ]
            monthly_goals = [
                {"id": "mo_volume_2500", "label": "Registrar 2500 Puntos de Volumen personal (corte de regalías)", "is_completed": False},
                {"id": "mo_sponsor_3", "label": "Patrocinar a 3 nuevos miembros/distribuidores", "is_completed": False}
            ]

        # Recommended channels and playlist links
        music_pref = distributor.coach_music_preference or 'spanish'
        music_url = "https://www.youtube.com/@billionairesound" if music_pref == 'spanish' else "https://www.youtube.com/@billionairesplaylist"
        
        resources = {
            'music_playlist': music_url,
            'music_playlist_label': "Billionaire Sound (Español)" if music_pref == 'spanish' else "Billionaire Playlist (English)",
            'eduardo_salazar_channel': "https://www.youtube.com/@MentalidadHBL",
            'metafisica_channel': "https://www.youtube.com/@audiolibrosdemetafisica",
            'recommended_books': meta.get('books', [])
        }

        data = {
            'level': level,
            'progress': meta.get('progress', 0),
            'coach_mode_enabled': distributor.coach_mode_enabled,
            'coach_music_preference': music_pref,
            'daily_challenges': daily_challenges,
            'weekly_goals': weekly_goals,
            'monthly_goals': monthly_goals,
            'resources': resources,
            'last_research_advice': distributor.coach_last_research_advice
        }

        return jsonify({'data': data}), 200

    except Exception as e:
        logger.error(f"Get roadmap error: {e}")
        return jsonify({'error': str(e)}), 500

@coach_bp.route('/settings', methods=['POST'])
@jwt_required()
def update_coach_settings():
    """Update distributor coach mode settings"""
    db.session.rollback()

    try:
        user, distributor = _get_current_distributor()
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Check if Coach Mode is being turned on
        was_enabled = bool(distributor.coach_mode_enabled)
        is_enabling = 'coach_mode_enabled' in data and bool(data['coach_mode_enabled']) and not was_enabled

        if 'coach_mode_enabled' in data:
            distributor.coach_mode_enabled = bool(data['coach_mode_enabled'])
        
        if 'coach_music_preference' in data:
            distributor.coach_music_preference = str(data['coach_music_preference'])
            
        if 'herbalife_level' in data:
            level = str(data['herbalife_level'])
            distributor.herbalife_level = level
            # Recalculate daily checklist if level changed
            distributor.coach_daily_tasks_status = ai_coach_service.generate_daily_tasks_checklist(level)
            # Recalculate progress index
            meta = ai_coach_service.get_level_metadata(level)
            distributor.coach_level_progress = meta.get('progress', 0)

        # Ensure checklist status is initialized
        level = distributor.herbalife_level or "Distribuidor Independiente"
        if not distributor.coach_daily_tasks_status:
            distributor.coach_daily_tasks_status = ai_coach_service.generate_daily_tasks_checklist(level)

        db.session.commit()
        
        # If Coach Mode is newly enabled, schedule today's checks and send a WhatsApp greeting
        if is_enabling:
            tz = pytz.timezone(distributor.timezone or 'America/Guayaquil')
            now_tz = datetime.now(tz)
            
            # 1. Schedule Midday at 2:00 PM local time if not passed
            midday_tz = now_tz.replace(hour=14, minute=0, second=0, microsecond=0)
            if now_tz < midday_tz:
                midday_utc = midday_tz.astimezone(pytz.utc).replace(tzinfo=None)
                CronService.schedule_followup(
                    distributor_id=distributor.id,
                    message="Coach Midday (Ad-hoc)",
                    scheduled_at=midday_utc,
                    action='coach_midday'
                )
                logger.info(f"Scheduled ad-hoc midday check for distributor {distributor.id}")
                
            # 2. Schedule Evening at 8:00 PM local time if not passed
            evening_tz = now_tz.replace(hour=20, minute=0, second=0, microsecond=0)
            if now_tz < evening_tz:
                evening_utc = evening_tz.astimezone(pytz.utc).replace(tzinfo=None)
                CronService.schedule_followup(
                    distributor_id=distributor.id,
                    message="Coach Evening (Ad-hoc)",
                    scheduled_at=evening_utc,
                    action='coach_evening'
                )
                logger.info(f"Scheduled ad-hoc evening check for distributor {distributor.id}")

            # 3. Send WhatsApp Welcome Notification with challenges list
            phone = distributor.whatsapp_phone or distributor.phone
            if phone:
                welcome_msg = (
                    f"🦁 *¡MODO COACH ENPIAI ACTIVADO!* 🦁\n\n"
                    f"Hola {distributor.name}, he activado tu entrenamiento personal diario rumbo al *Equipo del Presidente*.\n\n"
                    f"Tu nivel actual: *{level}*\n\n"
                    f"Te enviaré mensajes de seguimiento 3 veces al día en tu WhatsApp. Tus retos de hoy:\n"
                )
                lang_key = 'es' if (distributor.language or 'es') == 'es' else 'en'
                for i, t in enumerate(distributor.coach_daily_tasks_status.keys(), 1):
                    label = TASK_METADATA.get(t, {}).get(lang_key, t)
                    welcome_msg += f"{i}. {label}\n"
                
                # Add playlist info
                music_pref = distributor.coach_music_preference or 'spanish'
                music_url = "https://www.youtube.com/@billionairesound" if music_pref == 'spanish' else "https://www.youtube.com/@billionairesplaylist"
                welcome_msg += f"\n🎧 Tu playlist de reprogramación mental: {music_url}\n\n"
                welcome_msg += "¡La constancia diaria construye el éxito! Respóndeme a este chat al final del día informando tus avances. 🚀"
                
                try:
                    messaging_service.send_whatsapp(phone, welcome_msg, distributor.id)
                    logger.info(f"Welcome WhatsApp coach message sent to {phone}")
                except Exception as welcome_err:
                    logger.warning(f"Failed to send welcome WhatsApp coach message: {welcome_err}")

        logger.info(f"Coach settings updated for distributor {distributor.id}")
        return jsonify({'message': 'Settings updated successfully', 'data': distributor.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update coach settings error: {e}")
        return jsonify({'error': str(e)}), 500

@coach_bp.route('/tasks/toggle', methods=['POST'])
@jwt_required()
def toggle_task():
    """Toggle completion of a daily challenge task"""
    db.session.rollback()

    try:
        user, distributor = _get_current_distributor()
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        data = request.get_json()
        if not data or not data.get('task_id'):
            return jsonify({'error': 'task_id is required'}), 400

        task_id = data['task_id']
        tasks_status = dict(distributor.coach_daily_tasks_status or {})
        
        if task_id not in tasks_status:
            # Maybe standard fallback if task doesn't exist
            tasks_status[task_id] = False

        # Toggle state
        tasks_status[task_id] = not tasks_status[task_id]
        distributor.coach_daily_tasks_status = tasks_status
        db.session.commit()

        return jsonify({'message': 'Task status updated', 'data': {'task_id': task_id, 'is_completed': tasks_status[task_id]}}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Toggle task error: {e}")
        return jsonify({'error': str(e)}), 500

@coach_bp.route('/advice', methods=['POST'])
@jwt_required()
def request_advice():
    """Generates immediate AI Coach advice and sends it to WhatsApp"""
    db.session.rollback()

    try:
        user, distributor = _get_current_distributor()
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        level = distributor.herbalife_level or "Distribuidor Independiente"
        tasks_status = distributor.coach_daily_tasks_status or {}

        advice = ai_coach_service.generate_daily_coach_message(
            distributor_name=distributor.name,
            language=distributor.language or 'es',
            level=level,
            tasks_status=tasks_status
        )

        # Immediately send advice message to distributor WhatsApp
        phone = distributor.whatsapp_phone or distributor.phone
        if phone:
            try:
                messaging_service.send_whatsapp(
                    to_phone=phone,
                    message=f"🦁 *COACH ENPIAI - CONSEJO SOLICITADO*\n\n{advice}",
                    distributor_id=distributor.id
                )
                logger.info(f"Direct WhatsApp coach advice sent to {phone}")
            except Exception as wa_err:
                logger.warning(f"Failed to send direct WhatsApp coach advice: {wa_err}")

        return jsonify({'data': {'advice': advice}}), 200

    except Exception as e:
        logger.error(f"Request advice error: {e}")
        return jsonify({'error': str(e)}), 500

@coach_bp.route('/research', methods=['POST'])
@jwt_required()
def trigger_research():
    """Triggers the Roadmap Researcher Agent to validate distributor state and output tips"""
    db.session.rollback()

    try:
        user, distributor = _get_current_distributor()
        if not distributor:
            return jsonify({'error': 'Distributor not found'}), 404

        research_results = ai_coach_service.run_roadmap_research(distributor.id)
        if research_results.get('success'):
            # Persist research results advice in database
            distributor.coach_last_research_advice = research_results['analysis']
            db.session.commit()
            
            # Send roadmap advice summary to distributor WhatsApp
            phone = distributor.whatsapp_phone or distributor.phone
            if phone:
                try:
                    summary = (
                        f"🦁 *COACH ENPIAI - AUDITORÍA DE ROADMAP*\n\n"
                        f"Hola {distributor.name}, he completado la auditoría de tu Roadmap. "
                        f"Aquí están las recomendaciones estratégicas del Agente de Éxito:\n\n"
                        f"{research_results['analysis']}"
                    )
                    messaging_service.send_whatsapp(phone, summary, distributor.id)
                    logger.info(f"Direct WhatsApp roadmap advice sent to {phone}")
                except Exception as wa_err:
                    logger.warning(f"Failed to send direct WhatsApp roadmap advice: {wa_err}")

        return jsonify({'data': research_results}), 200

    except Exception as e:
        logger.error(f"Trigger research error: {e}")
        return jsonify({'error': str(e)}), 500
