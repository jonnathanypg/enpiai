from typing import List
from langchain_core.tools import StructuredTool
from flask import g
from .base_skill import BaseSkill
from services.email_service import email_service

class CommunicationSkill(BaseSkill):
    def __init__(self):
        self._name = "communication"
        self._description = "Send emails and messages."

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def get_tools(self) -> List[StructuredTool]:
        return [
            StructuredTool.from_function(
                func=self.send_email,
                name="send_email",
                description="Send an email to a user."
            )
        ]

    def send_email(self, to_email: str, subject: str, content: str) -> str:
        distributor = getattr(g, 'current_company', None)
        from_email = distributor.email if distributor else None
        
        success = email_service.send(to_email, subject, content, from_email=from_email)
        
        if success:
            return f"Email sent successfully to {to_email}."
        else:
            return "Failed to send email. Detailed logs checked."

    def get_system_prompt_addition(self) -> str:
        return "Use 'send_email' to send summaries, receipts, or requested information."
