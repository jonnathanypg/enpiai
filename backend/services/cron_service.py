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
        
        Args:
            distributor_id: Owner distributor
            message: The message to send when the task fires
            delay_minutes: Minutes from now (alternative to scheduled_at)
            scheduled_at: Exact datetime to fire
            conversation_id: Optional conversation context
            lead_id: Optional lead to contact
            channel: Target channel
            action: Type of action
            payload: Extra data for the action
            
        Returns:
            dict with task info
        """
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
        """Find and execute all tasks that are past their scheduled time."""
        now = datetime.utcnow()
        due_tasks = ScheduledTask.query.filter(
            ScheduledTask.status == 'pending',
            ScheduledTask.scheduled_at <= now,
        ).all()

        for task in due_tasks:
            try:
                self._execute_task(task)
                task.status = 'executed'
                task.executed_at = datetime.utcnow()
                logger.info(f"[CRON] Executed task #{task.id} ({task.action})")
            except Exception as e:
                task.status = 'failed'
                task.error_message = str(e)[:500]
                logger.error(f"[CRON] Task #{task.id} failed: {e}")
        
        if due_tasks:
            db.session.commit()

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
        else:
            logger.warning(f"[CRON] Unknown action: {task.action}")

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
