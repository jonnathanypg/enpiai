from extensions import ctx
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
            ),
            StructuredTool.from_function(
                func=self.send_whatsapp_message,
                name="send_whatsapp_message",
                description="[DISTRIBUTOR ONLY] Send a WhatsApp message to a specific phone number."
            )
        ]

    def send_whatsapp_message(self, phone: str, message: str) -> str:
        distributor = getattr(ctx, 'current_company', None)
        if not distributor:
            return "Error: context missing"
            
        from services.messaging_service import messaging_service
        success = messaging_service.send_whatsapp(phone, message, distributor.id)
        
        if success:
            return f"WhatsApp message sent successfully to {phone}."
        else:
            return f"Failed to send WhatsApp message to {phone}."

    def send_email(self, to_email: str, subject: str, content: str) -> str:
        distributor = getattr(ctx, 'current_company', None)
        from_email = distributor.email if distributor else None
        
        success = email_service.send(to_email, subject, content, from_email=from_email)
        
        if success:
            return f"Email sent successfully to {to_email}."
        else:
            return "Failed to send email. Detailed logs checked."

    def get_system_prompt_addition(self) -> str:
        return (
            "Use 'send_email' to send summaries, receipts, or requested information. "
            "Use 'send_whatsapp_message' when the distributor asks you to send a specific "
            "WhatsApp message to a lead or customer's phone number."
        )
