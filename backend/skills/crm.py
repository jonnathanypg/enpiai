import json
from typing import List
from langchain_core.tools import StructuredTool
from flask import g
from .base_skill import BaseSkill
from models.lead import Lead, LeadStatus, LeadSource
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
            ),
            StructuredTool.from_function(
                func=self.list_recent_leads,
                name="list_recent_leads",
                description="[DISTRIBUTOR ONLY] List the most recent leads for the distributor."
            ),
            StructuredTool.from_function(
                func=self.get_lead_details,
                name="get_lead_details",
                description="[DISTRIBUTOR ONLY] Get detailed information about a specific lead by ID or email."
            ),
            StructuredTool.from_function(
                func=self.toggle_ai_response,
                name="toggle_ai_response",
                description="[DISTRIBUTOR ONLY] Enable or disable automatic AI responses for a specific lead or customer."
            ),
            StructuredTool.from_function(
                func=self.mark_interested_in_buying,
                name="mark_interested_in_buying",
                description="Marks a lead as ready to buy and notifies the distributor to coordinate the sale."
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

    def register_lead(self, first_name: str, phone: str, last_name: str = "", email: str = None) -> str:
        distributor = getattr(g, 'current_company', None)
        conversation_id = getattr(g, 'current_conversation_id', None)
        
        if not distributor:
            return "Error: context missing"
            
        try:
            # Check for existing lead by phone first, then email
            existing = None
            if phone:
                existing = Lead.query.filter_by(distributor_id=distributor.id, phone=phone).first()
            if not existing and email:
                existing = Lead.query.filter_by(distributor_id=distributor.id, email=email).first()
                
            if existing:
                # Still link it to current conversation if unlinked
                if conversation_id:
                    from models.conversation import Conversation
                    conv = Conversation.query.get(conversation_id)
                    if conv and not conv.lead_id:
                        conv.lead_id = existing.id
                        db.session.commit()
                return f"Lead already exists with ID: {existing.id} (Phone/Email matched)."
                
            new_lead = Lead(
                distributor_id=distributor.id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                status=LeadStatus.NEW,
                source=LeadSource.AGENT_CHAT
            )
            db.session.add(new_lead)
            db.session.flush() # get ID without committing fully yet
            
            if conversation_id:
                from models.conversation import Conversation
                conv = Conversation.query.get(conversation_id)
                if conv:
                    conv.lead_id = new_lead.id
                    
            db.session.commit()
            return f"Successfully registered lead: {first_name} {last_name} and linked to the active conversation."
        except Exception as e:
            db.session.rollback()
            return f"Error registering lead: {str(e)}"

    def list_recent_leads(self, limit: int = 10) -> str:
        distributor = getattr(g, 'current_company', None)
        if not distributor:
            return "Error: context missing"
            
        leads = Lead.query.filter_by(distributor_id=distributor.id).order_by(Lead.created_at.desc()).limit(limit).all()
        if not leads:
            return "No leads found."
            
        result = []
        for l in leads:
            result.append(f"- ID: {l.id} | {l.name} ({l.status.value}) | Tel: {l.phone}")
            
        return "Recent Leads:\n" + "\n".join(result)

    def get_lead_details(self, lead_id: int = None, email: str = None) -> str:
        distributor = getattr(g, 'current_company', None)
        if not distributor:
            return "Error: context missing"
            
        lead = None
        if lead_id:
            lead = Lead.query.filter_by(id=lead_id, distributor_id=distributor.id).first()
        elif email:
            lead = Lead.query.filter_by(email=email, distributor_id=distributor.id).first()
            
        if not lead:
            return "Lead not found."
            
        details = [
            f"Details for {lead.name}:",
            f"Status: {lead.status.value}",
            f"Email: {lead.email}",
            f"Phone: {lead.phone}",
            f"Source: {lead.source.value}",
            f"Created: {lead.created_at.strftime('%Y-%m-%d')}",
            f"Score: {lead.score}/100"
        ]
        
        # Add latest note if exists
        try:
            latest_note = lead.note_records.order_by(Lead.created_at.desc()).first()
            if latest_note:
                details.append(f"Latest Note: {latest_note.content}")
        except: pass
            
        return "\n".join(details)

    def toggle_ai_response(self, target_type: str, target_id: int, enabled: bool) -> str:
        distributor = getattr(g, 'current_company', None)
        if not distributor:
            return "Error: context missing"
            
        if target_type.lower() == 'lead':
            record = Lead.query.filter_by(id=target_id, distributor_id=distributor.id).first()
        elif target_type.lower() == 'customer':
            record = Customer.query.filter_by(id=target_id, distributor_id=distributor.id).first()
        else:
            return "Error: target_type must be 'lead' or 'customer'."
            
        if not record:
            return f"Error: {target_type} not found."
            
        try:
            record.is_ai_active = enabled
            db.session.commit()
            state = "ENABLED" if enabled else "DISABLED"
            return f"Success: AI automated responses are now {state} for {record.full_name}."
        except Exception as e:
            db.session.rollback()
            return f"Error updating AI status: {str(e)}"

    def mark_interested_in_buying(self, lead_id: int, products_summary: str) -> str:
        distributor = getattr(g, 'current_company', None)
        if not distributor:
            return "Error: context missing"
            
        lead = Lead.query.filter_by(id=lead_id, distributor_id=distributor.id).first()
        if not lead:
            return "Error: Lead not found."
            
        try:
            # Update lead status
            lead.status = LeadStatus.QUALIFIED
            db.session.commit()
            
            # Send notification to distributor via WhatsApp
            from services.messaging_service import messaging_service
            
            distributor_phone = distributor.whatsapp_phone or distributor.phone
            if distributor_phone:
                notification_msg = (
                    f"🟢 *ALERTA DE VENTA*\n"
                    f"El lead *{lead.full_name}* está listo para comprar.\n"
                    f"Teléfono: {lead.phone}\n"
                    f"Email: {lead.email}\n"
                    f"Interés: {products_summary}\n\n"
                    f"Por favor contáctalo para cerrar la venta."
                )
                messaging_service.send_whatsapp(distributor_phone, notification_msg, distributor.id)
                return "Successfully marked lead as qualified and notified the distributor."
            else:
                return "Successfully marked lead as qualified, but could not notify distributor (no WhatsApp phone configured)."
        except Exception as e:
            db.session.rollback()
            return f"Error marking interest: {str(e)}"

    def get_system_prompt_addition(self) -> str:
        return "Use 'lookup_customer' to verify identity. Use 'register_lead' to add new potential clients. Distributors can use 'list_recent_leads', 'get_lead_details', and 'toggle_ai_response'. Agents should use 'mark_interested_in_buying' when a prospect is ready to buy."
