import json
from datetime import datetime
from typing import List
from langchain_core.tools import StructuredTool
from flask import g
from extensions import db, ctx
from .base_skill import BaseSkill

class CronSkill(BaseSkill):
    """
    Provides tools for scheduling follow-up messages and reminders.
    The agent can use these to ensure no lead falls through the cracks.
    """
    def __init__(self):
        self._name = "cron"
        self._description = "Schedule follow-up messages and reminders for future delivery."

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def get_tools(self) -> List[StructuredTool]:
        return [
            StructuredTool.from_function(
                func=self.schedule_followup,
                name="schedule_followup",
                description="Schedule a follow-up message to be sent later."
            ),
            StructuredTool.from_function(
                func=self.list_pending_followups,
                name="list_pending_followups",
                description="List all pending scheduled follow-ups for this distributor."
            ),
            StructuredTool.from_function(
                func=self.cancel_followup,
                name="cancel_followup",
                description="Cancel a pending scheduled follow-up by its ID."
            )
        ]

    def schedule_followup(self, message: str, delay_minutes: int = 1440, channel: str = 'whatsapp') -> str:
        """
        Schedule a follow-up message to be sent later.
        Use this when a lead says they'll think about it, or when you want to check in after a few days.
        
        Args:
            message: The follow-up message to send
            delay_minutes: How many minutes from now to send (default: 1440 = 24 hours)
            channel: 'whatsapp' or 'email'
        """
        db.session.rollback()
        distributor = getattr(ctx, 'current_company', None)
        conversation_id = getattr(ctx, 'current_conversation_id', None)
        
        if not distributor:
            return "Error: context missing"
            
        # Try to find lead_id from conversation if possible
        lead_id = None
        try:
            from models.conversation import Conversation
            conv = Conversation.query.get(conversation_id)
            if conv:
                lead_id = conv.lead_id
        except Exception as e:
            logging.debug(f"Could not resolve lead_id from conversation: {e}")

        from services.cron_service import CronService
        result = CronService.schedule_followup(
            distributor_id=distributor.id,
            message=message,
            delay_minutes=delay_minutes,
            conversation_id=conversation_id,
            lead_id=lead_id,
            channel=channel,
            action='send_message',
        )
        if result.get('success'):
            return f"✅ Follow-up scheduled for {result['scheduled_at']} (Task #{result['task_id']})"
        return f"❌ Failed to schedule: {result.get('error', 'Unknown error')}"

    def list_pending_followups(self) -> str:
        """List all pending scheduled follow-ups for this distributor."""
        db.session.rollback()
        distributor = getattr(ctx, 'current_company', None)
        if not distributor:
            return "Error: context missing"
            
        from services.cron_service import CronService
        tasks = CronService.list_pending(distributor.id)
        if not tasks:
            return "No pending follow-ups."
        lines = [f"- #{t['id']}: '{t['message'][:50]}...' at {t['scheduled_at']} via {t['channel']}" for t in tasks]
        return f"Pending follow-ups ({len(tasks)}):\n" + "\n".join(lines)

    def cancel_followup(self, task_id: int) -> str:
        """Cancel a pending scheduled follow-up by its ID."""
        db.session.rollback()
        distributor = getattr(ctx, 'current_company', None)
        if not distributor:
            return "Error: context missing"
            
        from services.cron_service import CronService
        result = CronService.cancel_task(task_id, distributor.id)
        if result.get('success'):
            return f"✅ Task #{task_id} cancelled."
        return f"❌ {result.get('error', 'Unknown error')}"

    def get_system_prompt_addition(self) -> str:
        return (
            "You can schedule follow-up messages using the `schedule_followup` tool. "
            "Use this when a lead says they'll think about it, asks to be contacted later, "
            "or when you finish a conversation and want to check back in 24-48 hours. "
            "Default is 24 hours (1440 minutes). You can also list and cancel pending follow-ups."
        )

