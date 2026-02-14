import json
from typing import List
from langchain_core.tools import StructuredTool
from flask import g
from .base_skill import BaseSkill
from models.lead import Lead, LeadStatus
from models.customer import Customer
from extensions import db

class CRMSkill(BaseSkill):
    def __init__(self):
        self._name = "crm"
        self._description = "Manage leads and look up customers."

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def get_tools(self) -> List[StructuredTool]:
        return [
            StructuredTool.from_function(
                func=self.lookup_customer,
                name="lookup_customer",
                description="Look up a customer or lead by email."
            ),
            StructuredTool.from_function(
                func=self.register_lead,
                name="register_lead",
                description="Register a new prospect/lead in the system."
            )
        ]

    def lookup_customer(self, email: str) -> str:
        distributor = getattr(g, 'current_company', None)
        if not distributor:
            return "Error: context missing"
            
        customer = Customer.query.filter_by(distributor_id=distributor.id, email=email).first()
        if customer:
            return json.dumps({
                "status": "found",
                "type": "customer",
                "name": f"{customer.first_name} {customer.last_name}",
                "id": customer.id
            })
            
        lead = Lead.query.filter_by(distributor_id=distributor.id, email=email).first()
        if lead:
            return json.dumps({
                "status": "found",
                "type": "lead",
                "name": f"{lead.first_name} {lead.last_name}",
                "id": lead.id
            })
            
        return json.dumps({"status": "not_found", "message": "User not found in records."})

    def register_lead(self, first_name: str, last_name: str, email: str, phone: str = None) -> str:
        distributor = getattr(g, 'current_company', None)
        if not distributor:
            return "Error: context missing"
            
        try:
            existing = Lead.query.filter_by(distributor_id=distributor.id, email=email).first()
            if existing:
                return f"Lead already exists with ID: {existing.id}"
                
            new_lead = Lead(
                distributor_id=distributor.id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                status=LeadStatus.NEW,
                source="agent_chat"
            )
            db.session.add(new_lead)
            db.session.commit()
            return f"Successfully registered lead: {first_name} {last_name}"
        except Exception as e:
            db.session.rollback()
            return f"Error registering lead: {str(e)}"

    def get_system_prompt_addition(self) -> str:
        return "Use 'lookup_customer' to verify identity. Use 'register_lead' to add new potential clients."
