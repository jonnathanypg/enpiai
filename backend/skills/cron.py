"""
Cron Skill — Allows the agent to schedule future follow-ups and reminders.
This gives the agent proactive capabilities instead of being purely reactive.
"""
import json
from datetime import datetime
from langchain.tools import tool
from skills.base_skill import BaseSkill


class CronSkill(BaseSkill):
    """
    Provides tools for scheduling follow-up messages and reminders.
    The agent can use these to ensure no lead falls through the cracks.
    """

    name = "cron"
    description = "Schedule follow-up messages and reminders for future delivery."

    def get_tools(self, context: dict = None):
        distributor_id = context.get('distributor_id') if context else None
        conversation_id = context.get('conversation_id') if context else None
        lead_id = context.get('lead_id') if context else None

        @tool
        def schedule_followup(message: str, delay_minutes: int = 1440, channel: str = 'whatsapp') -> str:
            """
            Schedule a follow-up message to be sent later.
            Use this when a lead says they'll think about it, or when you want to check in after a few days.
            
            Args:
                message: The follow-up message to send
                delay_minutes: How many minutes from now to send (default: 1440 = 24 hours)
                channel: 'whatsapp' or 'email'
            """
            from services.cron_service import CronService
            result = CronService.schedule_followup(
                distributor_id=distributor_id,
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

        @tool
        def list_pending_followups() -> str:
            """List all pending scheduled follow-ups for this distributor."""
            from services.cron_service import CronService
            tasks = CronService.list_pending(distributor_id)
            if not tasks:
                return "No pending follow-ups."
            lines = [f"- #{t['id']}: '{t['message'][:50]}...' at {t['scheduled_at']} via {t['channel']}" for t in tasks]
            return f"Pending follow-ups ({len(tasks)}):\n" + "\n".join(lines)

        @tool
        def cancel_followup(task_id: int) -> str:
            """Cancel a pending scheduled follow-up by its ID."""
            from services.cron_service import CronService
            result = CronService.cancel_task(task_id, distributor_id)
            if result.get('success'):
                return f"✅ Task #{task_id} cancelled."
            return f"❌ {result.get('error', 'Unknown error')}"

        return [schedule_followup, list_pending_followups, cancel_followup]

    def get_system_prompt_addition(self) -> str:
        return (
            "You can schedule follow-up messages using the `schedule_followup` tool. "
            "Use this when a lead says they'll think about it, asks to be contacted later, "
            "or when you finish a conversation and want to check back in 24-48 hours. "
            "Default is 24 hours (1440 minutes). You can also list and cancel pending follow-ups."
        )
