from typing import List
from datetime import datetime, timedelta
from langchain_core.tools import StructuredTool
from flask import g
from .base_skill import BaseSkill
from services.google_service import google_service
from models.lead import Lead
from models.customer import Customer
from models.appointment import Appointment
from extensions import db

class SchedulerSkill(BaseSkill):
    def __init__(self):
        self._name = "scheduler"
        self._description = "Manage calendar appointments and check availability."

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def get_tools(self) -> List[StructuredTool]:
        return [
            StructuredTool.from_function(
                func=self.check_availability,
                name="check_availability",
                description="Check calendar availability for a specific date."
            ),
            StructuredTool.from_function(
                func=self.schedule_appointment,
                name="schedule_appointment",
                description="Schedule a meeting on Google Calendar after user confirmation."
            )
        ]

    def check_availability(self, date: str, preferred_time: str = None) -> str:
        """
        Check calendar availability for a specific date (YYYY-MM-DD).
        """
        distributor = getattr(g, 'current_company', None)
        if not distributor:
            return "Error: No distributor context found."

        result = google_service.check_availability(
            distributor, 
            date, 
            timezone=distributor.timezone or 'America/Guayaquil'
        )
        
        if 'error' in result:
            return f"Error checking calendar: {result['error']}"
            
        slots = result.get('available_slots', [])
        if not slots:
            return f"No slots available on {date}."
            
        if preferred_time:
            if preferred_time in slots:
                return f"✅ {preferred_time} is available on {date}."
            else:
                return f"❌ {preferred_time} is NOT available. Available times: {', '.join(slots[:5])}..."
                
        return f"Available slots on {date}: {', '.join(slots)}"

    def schedule_appointment(self, date: str, time: str, email: str, topic: str) -> str:
        """
        Schedule a meeting on Google Calendar.
        """
        distributor = getattr(g, 'current_company', None)
        if not distributor:
            return "Error: No distributor context found."

        try:
            start_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        except ValueError:
            return "Invalid date/time format. Use YYYY-MM-DD and HH:MM."
            
        result = google_service.create_event(
            distributor=distributor,
            title=f"Meeting with {email}: {topic}",
            start_datetime=start_datetime,
            duration_minutes=30,
            description=f"Scheduled via AI Agent.\nTopic: {topic}",
            attendee_email=email,
            timezone=distributor.timezone or 'America/Guayaquil'
        )
        
        if 'error' in result:
            return f"Failed to schedule: {result['error']}"
            
        # Save to local DB
        lead = Lead.query.filter_by(distributor_id=distributor.id, email=email).first()
        customer = Customer.query.filter_by(distributor_id=distributor.id, email=email).first()
        
        appt = Appointment(
            distributor_id=distributor.id,
            title=topic,
            scheduled_at=start_datetime,
            duration_minutes=30,
            status='scheduled',
            google_event_id=result.get('event_id'),
            lead_id=lead.id if lead else None,
            customer_id=customer.id if customer else None
        )
        db.session.add(appt)
        db.session.commit()
        
        return f"Appointment scheduled successfully for {date} at {time}. Link: {result.get('html_link')}"

    def get_system_prompt_addition(self) -> str:
        return (
            "You have access to a calendar. "
            "Use 'check_availability' before 'schedule_appointment'. "
            "Always confirm the time with the user."
        )
