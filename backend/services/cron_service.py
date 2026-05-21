"""
Cron / Scheduled Tasks Service
Manages background follow-ups and proactive agent actions.
Inspired by openclaw's cron protocol.

Migration Path: Tasks will be distributed across P2P nodes with consensus-based scheduling.
"""
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional
from extensions import db

logger = logging.getLogger(__name__)


class ScheduledTask(db.Model):
    """Persistent task record for scheduled follow-ups."""
    __tablename__ = 'scheduled_tasks'

    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    
    # Task Configuration
    action = db.Column(db.String(50), nullable=False)  # 'send_message', 'send_email', 'check_in'
    payload = db.Column(db.JSON, nullable=True)         # Action-specific data
    message = db.Column(db.Text, nullable=True)         # Message to send
    channel = db.Column(db.String(20), default='whatsapp')  # Target channel
    
    # Scheduling
    scheduled_at = db.Column(db.DateTime, nullable=False)   # When to fire
    executed_at = db.Column(db.DateTime, nullable=True)     # When it actually ran  
    status = db.Column(db.String(20), default='pending')    # pending, executed, failed, cancelled
    error_message = db.Column(db.Text, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(20), default='agent')  # 'agent' or 'user'

    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'message': self.message,
            'channel': self.channel,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'status': self.status,
        }


class CronService:
    """
    Background service that checks for due tasks and executes them.
    Runs as a daemon thread within the Flask process.
    """
    
    _instance = None
    _running = False
    _thread = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------ #
    #  TASK CREATION (called by skills/agent)                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def cancel_conversation_tasks(conversation_id: int, action: str = None) -> int:
        """Cancel all pending tasks for a specific conversation."""
        query = ScheduledTask.query.filter_by(conversation_id=conversation_id, status='pending')
        if action:
            query = query.filter_by(action=action)
        
        tasks = query.all()
        for t in tasks:
            t.status = 'cancelled'
        
        try:
            db.session.commit()
            if tasks:
                logger.info(f"[CRON] Cancelled {len(tasks)} pending tasks for conv {conversation_id}")
            return len(tasks)
        except Exception as e:
            db.session.rollback()
            logger.error(f"[CRON] Failed to cancel tasks for conv {conversation_id}: {e}")
            return 0

    @staticmethod
    def schedule_followup(
        distributor_id: int,
        message: str,
        delay_minutes: int = 0,
        scheduled_at: Optional[datetime] = None,
        conversation_id: int = None,
        lead_id: int = None,
        channel: str = 'whatsapp',
        action: str = 'send_message',
        payload: dict = None,
    ) -> dict:
        """
        Schedule a follow-up task. 
        Automatically cancels previous pending 'auto_followup' tasks for the same conversation.
        """
        if conversation_id and action == 'auto_followup':
            CronService.cancel_conversation_tasks(conversation_id, action='auto_followup')

        if scheduled_at is None:
            scheduled_at = datetime.utcnow() + timedelta(minutes=max(1, delay_minutes))
        
        task = ScheduledTask(
            distributor_id=distributor_id,
            conversation_id=conversation_id,
            lead_id=lead_id,
            action=action,
            message=message,
            channel=channel,
            payload=payload or {},
            scheduled_at=scheduled_at,
            status='pending',
            created_by='agent',
        )
        
        try:
            db.session.add(task)
            db.session.commit()
            logger.info(f"[CRON] Scheduled task #{task.id}: '{action}' at {scheduled_at}")
            return {'success': True, 'task_id': task.id, 'scheduled_at': scheduled_at.isoformat()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"[CRON] Failed to schedule task: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def cancel_task(task_id: int, distributor_id: int) -> dict:
        """Cancel a pending scheduled task."""
        task = ScheduledTask.query.filter_by(id=task_id, distributor_id=distributor_id, status='pending').first()
        if not task:
            return {'success': False, 'error': 'Task not found or already executed'}
        task.status = 'cancelled'
        db.session.commit()
        logger.info(f"[CRON] Cancelled task #{task_id}")
        return {'success': True}

    @staticmethod
    def list_pending(distributor_id: int) -> list:
        """List all pending tasks for a distributor."""
        tasks = ScheduledTask.query.filter_by(distributor_id=distributor_id, status='pending').order_by(ScheduledTask.scheduled_at).all()
        return [t.to_dict() for t in tasks]

    # ------------------------------------------------------------------ #
    #  BACKGROUND WORKER                                                  #
    # ------------------------------------------------------------------ #

    def start_worker(self, app):
        """Start the background cron worker thread."""
        if CronService._running:
            logger.info("[CRON] Worker already running.")
            return

        CronService._running = True
        CronService._thread = threading.Thread(target=self._worker_loop, args=(app,), daemon=True)
        CronService._thread.start()
        logger.info("[CRON] Background worker started.")

    def stop_worker(self):
        """Signal the worker to stop."""
        CronService._running = False
        logger.info("[CRON] Worker stop requested.")

    def _worker_loop(self, app):
        """Main loop: check for due tasks every 30 seconds."""
        while CronService._running:
            try:
                with app.app_context():
                    self._process_due_tasks()
            except Exception as e:
                logger.error(f"[CRON] Worker error: {e}")
            time.sleep(30)

    def _process_due_tasks(self):
        """
        Find and execute all tasks that are past their scheduled time.
        Uses a 'claim-first' strategy to be safe for multiple workers.
        """
        db.session.rollback()  # Mandatory first line per GEMINI.md protocol
        now = datetime.utcnow()
        
        # 1. Fetch due tasks. 
        # We use a smaller batch size and with_for_update(skip_locked=True) 
        # to ensure multiple workers don't collide.
        try:
            due_tasks = ScheduledTask.query.filter(
                ScheduledTask.status == 'pending',
                ScheduledTask.scheduled_at <= now,
            ).with_for_update(skip_locked=True).limit(20).all()
            
            if not due_tasks:
                return

            for task in due_tasks:
                try:
                    # 2. Claim the task IMMEDIATELY by marking it as executed
                    # This prevents other workers from picking it up if they query 
                    # while we are executing (though skip_locked should handle it).
                    task.status = 'executed'
                    task.executed_at = datetime.utcnow()
                    db.session.commit()

                    # 3. Actually run the logic
                    self._execute_task(task)
                    logger.info(f"[CRON] Executed task #{task.id} ({task.action})")
                    
                except Exception as e:
                    logger.error(f"[CRON] Task #{task.id} failed: {e}")
                    # Re-open session and mark as failed if it wasn't a commit error
                    try:
                        db.session.rollback()
                        task = ScheduledTask.query.get(task.id)
                        if task:
                            task.status = 'failed'
                            task.error_message = str(e)[:500]
                            db.session.commit()
                    except Exception as rb_err:
                        logger.error(f"[CRON] Could not mark task as failed: {rb_err}")
                        db.session.rollback()
        except Exception as e:
            logger.error(f"[CRON] Error in _process_due_tasks: {e}")
            db.session.rollback()

    def _execute_task(self, task: ScheduledTask):
        """
        Execute a single scheduled task.
        Routes to the appropriate handler based on task.action.
        """
        if task.action == 'send_message':
            self._handle_send_message(task)
        elif task.action == 'send_email':
            self._handle_send_email(task)
        elif task.action == 'check_in':
            self._handle_check_in(task)
        elif task.action == 'daily_summary':
            self._handle_daily_summary(task)
        elif task.action == 'auto_followup':
            self._handle_auto_followup(task)
        else:
            logger.warning(f"[CRON] Unknown action: {task.action}")

    def _handle_daily_summary(self, task: ScheduledTask):
        """Generates and sends the morning summary to the distributor."""
        from models.distributor import Distributor
        from services.messaging_service import messaging_service
        from skills.crm import CRMSkill
        import pytz
        
        distributor = Distributor.query.get(task.distributor_id)
        if not distributor: return

        # Use CRMSkill to generate the report
        from flask import g
        g.current_company = distributor
        
        crm = CRMSkill()
        report = crm.get_business_summary_report()
        
        dist_phone = distributor.whatsapp_phone or distributor.phone
        if dist_phone:
            header = "☀️ *¡BUENOS DÍAS! AQUÍ TU RESUMEN MATUTINO*\n\n"
            messaging_service.send_whatsapp(dist_phone, header + report, distributor.id)
            
        # Schedule next day's summary in distributor's timezone
        tz = pytz.timezone(distributor.timezone or 'America/Guayaquil')
        now_tz = datetime.now(tz)
        
        # Calculate next 8:00 AM in local time
        next_run_tz = now_tz.replace(hour=8, minute=0, second=0, microsecond=0)
        if next_run_tz <= now_tz:
            next_run_tz += timedelta(days=1)
            
        # Convert back to UTC for storage in DB
        next_run_utc = next_run_tz.astimezone(pytz.utc).replace(tzinfo=None)
        
        self.schedule_followup(
            distributor_id=distributor.id,
            message="Morning Summary",
            scheduled_at=next_run_utc,
            action='daily_summary'
        )

    def _handle_auto_followup(self, task: ScheduledTask):
        """Sends an automatic follow-up only if the user hasn't replied yet."""
        from models.conversation import Conversation, Message, MessageRole
        from services.messaging_service import messaging_service
        
        conv = Conversation.query.get(task.conversation_id)
        if not conv: return

        # CHECK: Did the user send a message after our task was scheduled?
        # If the last message is from the user, we DON'T send an auto-followup 
        # because the user already replied or the conversation is active.
        # But wait, the logic is: if last message is from AI, then user hasn't replied.
        last_msg = Message.query.filter_by(conversation_id=conv.id).order_by(Message.created_at.desc()).first()
        
        if last_msg and last_msg.role == MessageRole.ASSISTANT:
            # User hasn't replied to our last AI message!
            dist_phone = task.payload.get('distributor_phone')
            lead_phone = task.payload.get('lead_phone')
            
            if lead_phone:
                messaging_service.send_whatsapp(lead_phone, task.message, task.distributor_id)
                logger.info(f"[CRON] Auto-followup sent to {lead_phone} for conv {conv.id}")

    def _handle_send_message(self, task: ScheduledTask):
        """Send a WhatsApp or Telegram message."""
        if not task.lead_id:
            logger.warning(f"[CRON] Task #{task.id}: No lead_id for send_message")
            return
        
        from models.lead import Lead
        lead = Lead.query.get(task.lead_id)
        if not lead or not lead.phone:
            logger.warning(f"[CRON] Task #{task.id}: Lead not found or has no phone")
            return

        if task.channel == 'whatsapp':
            import requests
            from flask import current_app
            wa_url = current_app.config.get('WHATSAPP_API_URL', 'http://localhost:3001')
            try:
                requests.post(f"{wa_url}/lead/send", json={
                    'phone': lead.phone,
                    'message': task.message,
                    'distributorId': str(task.distributor_id),
                }, timeout=10)
            except Exception as e:
                logger.error(f"[CRON] WhatsApp send failed: {e}")
                raise

    def _handle_send_email(self, task: ScheduledTask):
        """Send email follow-up."""
        payload = task.payload or {}
        to_email = payload.get('to_email')
        subject = payload.get('subject', 'Follow-up')
        if not to_email:
            logger.warning(f"[CRON] Task #{task.id}: No to_email in payload")
            return
        from services.email_service import EmailService
        EmailService.send_email(to_email=to_email, subject=subject, body=task.message)

    def _handle_check_in(self, task: ScheduledTask):
        """
        Check-in: query lead status and log. 
        Future: could trigger a proactive message if lead hasn't responded.
        """
        logger.info(f"[CRON] Check-in for lead #{task.lead_id} (distributor #{task.distributor_id})")

    def _handle_send_email(self, task: ScheduledTask):
        """Send email follow-up."""
        payload = task.payload or {}
        to_email = payload.get('to_email')
        subject = payload.get('subject', 'Follow-up')
        if not to_email:
            logger.warning(f"[CRON] Task #{task.id}: No to_email in payload")
            return
        from services.email_service import EmailService
        EmailService.send_email(to_email=to_email, subject=subject, body=task.message)

    def _handle_check_in(self, task: ScheduledTask):
        """
        Check-in: query lead status and log. 
        Future: could trigger a proactive message if lead hasn't responded.
        """
        logger.info(f"[CRON] Check-in for lead #{task.lead_id} (distributor #{task.distributor_id})")
