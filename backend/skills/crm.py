import json
import logging
from typing import List
from datetime import datetime
from langchain_core.tools import StructuredTool
from flask import g
from .base_skill import BaseSkill
from models.lead import Lead, LeadStatus, LeadSource
from models.customer import Customer
from models.wellness_evaluation import WellnessEvaluation
from extensions import db, ctx

logger = logging.getLogger(__name__)

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
            ),
            StructuredTool.from_function(
                func=self.request_human_contact,
                name="request_human_contact",
                description="Use when the lead wants a phone call, to speak with a human/agent, or needs personal assistance from the distributor."
            ),
            StructuredTool.from_function(
                func=self.list_active_conversations,
                name="list_active_conversations",
                description="[DISTRIBUTOR ONLY] List recent active conversations with leads."
            ),
            StructuredTool.from_function(
                func=self.get_conversation_history,
                name="get_conversation_history",
                description="[DISTRIBUTOR ONLY] Get the message history of a specific conversation by ID."
            ),
            StructuredTool.from_function(
                func=self.get_business_summary_report,
                name="get_business_summary_report",
                description="[DISTRIBUTOR ONLY] Get a comprehensive summary of today's activity: new leads, active chats, and people ready to buy."
            ),
            StructuredTool.from_function(
                func=self.add_crm_note,
                name="add_crm_note",
                description="Adds a persistent note, plan, or summary to a lead or customer record."
            )
        ]

    def get_business_summary_data(self) -> dict:
        """Retrieves structured data for the business summary report."""
        db.session.rollback()
        distributor = getattr(ctx, 'current_company', None)
        if not distributor:
            return {"error": "context_missing"}
            
        from datetime import datetime, time, timedelta
        # Today in UTC
        today_start = datetime.combine(datetime.utcnow().date(), time.min)
        
        try:
            # 1. New Leads Today
            new_leads = Lead.query.filter(
                Lead.distributor_id == distributor.id,
                Lead.created_at >= today_start
            ).all()
            
            # 2. People interested in buying (status QUALIFIED)
            ready_to_buy = Lead.query.filter(
                Lead.distributor_id == distributor.id,
                Lead.status == LeadStatus.QUALIFIED
            ).all()
            
            # 3. Active Conversations with pending user messages
            from models.conversation import Conversation, Message, MessageRole
            convs = Conversation.query.filter(
                Conversation.distributor_id == distributor.id,
                Conversation.last_message_at >= today_start
            ).order_by(Conversation.last_message_at.desc()).all()

            # 4. Appointments Today
            from models.appointment import Appointment
            appointments = Appointment.query.filter(
                Appointment.distributor_id == distributor.id,
                Appointment.scheduled_at >= today_start,
                Appointment.scheduled_at < today_start + timedelta(days=1)
            ).all()

            # 5. Wellness Evaluations Today
            from models.wellness_evaluation import WellnessEvaluation
            evaluations = WellnessEvaluation.query.filter(
                WellnessEvaluation.distributor_id == distributor.id,
                WellnessEvaluation.created_at >= today_start
            ).all()
            
            return {
                "distributor_id": distributor.id,
                "date": datetime.utcnow().date().isoformat(),
                "new_leads": [l.to_dict() for l in new_leads],
                "ready_to_buy": [l.to_dict() for l in ready_to_buy],
                "active_convs": [c.id for c in convs], 
                "active_convs_details": [],
                "appointments": [a.to_dict() for a in appointments],
                "wellness_evaluations": [e.id for e in evaluations],
                "counts": {
                    "new_leads": len(new_leads),
                    "ready_to_buy": len(ready_to_buy),
                    "active_convs": len(convs),
                    "appointments": len(appointments),
                    "wellness_evaluations": len(evaluations)
                }
            }
        except Exception as e:
            logger.error(f"Error gathering summary data: {e}")
            return {"error": str(e)}

    def get_business_summary_report(self) -> str:
        data = self.get_business_summary_data()
        if "error" in data:
            return f"Error al generar reporte: {data['error']}"
            
        counts = data["counts"]
        report = [f"📊 RESUMEN DE NEGOCIO - {data['date']}"]
        
        if counts["new_leads"] > 0:
            report.append(f"\n✅ LEADS NUEVOS HOY ({counts['new_leads']}):")
            for l in data["new_leads"]:
                report.append(f"- {l['first_name']} {l['last_name']} ({l['phone']})")
        
        if counts["wellness_evaluations"] > 0:
            report.append(f"\n📝 EVALUACIONES COMPLETADAS ({counts['wellness_evaluations']})")
            report.append("  (Los prospectos ya recibieron su reporte PDF)")

        if counts["ready_to_buy"] > 0:
            report.append(f"\n💰 LISTOS PARA COMPRAR ({counts['ready_to_buy']}):")
            for l in data["ready_to_buy"]:
                report.append(f"- {l['first_name']} {l['last_name']} ({l['phone']})")

        if counts["appointments"] > 0:
            report.append(f"\n📅 CITAS HOY ({counts['appointments']}):")
            for a in data["appointments"]:
                time_str = a['scheduled_at'][11:16] if a['scheduled_at'] else "N/A"
                report.append(f"- {time_str}: {a['title']}")

        if counts["active_convs"] > 0:
            report.append(f"\n💬 CHATS ACTIVOS ({counts['active_convs']})")
            # We don't list all for brevity in the summary if there are many
            
        if sum(counts.values()) == 0:
            return "" # Return empty if no data, caller will handle with Coach Message
            
        return "\n".join(report)

    def add_crm_note(self, target_type: str, target_id: int, content: str) -> str:
        db.session.rollback()
        distributor = getattr(ctx, 'current_company', None)
        if not distributor:
            return "Error: context missing"
            
        try:
            from models.note import Note
            new_note = Note(
                distributor_id=distributor.id,
                content=content
            )
            
            if target_type.lower() == 'lead':
                new_note.lead_id = target_id
            elif target_type.lower() == 'customer':
                new_note.customer_id = target_id
            else:
                return "Error: target_type must be 'lead' or 'customer'."
                
            db.session.add(new_note)
            db.session.commit()
            return f"Note successfully added to {target_type} #{target_id}."
        except Exception as e:
            db.session.rollback()
            return f"Error adding note: {str(e)}"

    def list_active_conversations(self, limit: int = 10) -> str:
        db.session.rollback()
        distributor = getattr(ctx, 'current_company', None)
        if not distributor:
            return "Error: context missing"
            
        try:
            from models.conversation import Conversation, Message, MessageRole
            convs = Conversation.query.filter_by(distributor_id=distributor.id).order_by(Conversation.last_message_at.desc()).limit(limit).all()
            if not convs:
                return "No active conversations found."
                
            result = []
            for c in convs:
                participant = c.participant_name or c.participant_id or "Desconocido"
                # Check if last message was from User (meaning it might be unread/pending for the human distributor)
                last_msg = Message.query.filter_by(conversation_id=c.id).order_by(Message.created_at.desc()).first()
                status = " [PND]" if last_msg and last_msg.role == MessageRole.USER else ""
                
                result.append(f"- ID: {c.id} | Participante: {participant}{status} | Canal: {c.channel.value} | Último: {c.last_message_at.strftime('%m-%d %H:%M')}")
            
            return "Active Conversations ([PND] = Pending human reply):\n" + "\n".join(result)
        except Exception as e:
            return f"Error listing conversations: {str(e)}"

    def get_conversation_history(self, conversation_id: int, limit: int = 20) -> str:
        db.session.rollback()
        distributor = getattr(ctx, 'current_company', None)
        if not distributor:
            return "Error: context missing"
            
        try:
            from models.conversation import Conversation, Message
            conv = Conversation.query.filter_by(id=conversation_id, distributor_id=distributor.id).first()
            if not conv:
                return "Conversation not found or access denied."
                
            messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at.desc()).limit(limit).all()
            messages.reverse() # Show in chronological order
            
            history = [f"History for Conversation #{conversation_id} ({conv.participant_name}):"]
            for m in messages:
                history.append(f"[{m.created_at.strftime('%H:%M')}] {m.role.value.upper()}: {m.content}")
                
            return "\n".join(history)
        except Exception as e:
            return f"Error retrieving history: {str(e)}"

    def request_human_contact(self, summary: str, recommendation: str = "") -> str:
        db.session.rollback()
        distributor = getattr(ctx, 'current_company', None)
        conversation_id = getattr(ctx, 'current_conversation_id', None)
        
        if not distributor:
            return "Error: context missing"
            
        try:
            from models.conversation import Conversation
            conv = Conversation.query.get(conversation_id)
            lead_name = conv.participant_name if conv else "Un prospecto"
            lead_phone = conv.participant_id if conv else "No disponible"
            
            # Send notification to distributor
            from services.messaging_service import messaging_service
            distributor_phone = distributor.whatsapp_phone or distributor.phone
            
            if distributor_phone:
                notification_msg = (
                    f"🚨 *SOLICITUD DE CONTACTO HUMANO*\n"
                    f"El prospecto *{lead_name}* ({lead_phone}) solicita hablar contigo.\n\n"
                    f"*Resumen:* {summary}\n"
                    f"*Tu recomendación IA:* {recommendation}\n\n"
                    f"Por favor, contáctalo lo antes posible."
                )
                messaging_service.send_whatsapp(distributor_phone, notification_msg, distributor.id)
                return "He notificado a mi supervisor. Se pondrá en contacto contigo a la brevedad."
            else:
                return "He registrado tu solicitud de contacto, pero no pude notificar al supervisor en este momento."
        except Exception as e:
            return f"Error al procesar solicitud: {str(e)}"

    def lookup_customer(self, email: str) -> str:
        db.session.rollback()
        distributor = getattr(ctx, 'current_company', None)
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
        db.session.rollback()
        distributor = getattr(ctx, 'current_company', None)
        conversation_id = getattr(ctx, 'current_conversation_id', None)
        
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

            # Notify distributor about new lead via WhatsApp and Email
            try:
                distributor_phone = distributor.whatsapp_phone or distributor.phone
                if distributor_phone:
                    from services.messaging_service import messaging_service
                    notification_msg = (
                        f"🆕 *NUEVO LEAD REGISTRADO*\n"
                        f"Nombre: *{first_name} {last_name}*\n"
                        f"Teléfono: {phone}\n"
                        f"Email: {email or 'No provisto'}\n\n"
                        f"El sistema ha comenzado el seguimiento automático."
                    )
                    messaging_service.send_whatsapp(distributor_phone, notification_msg, distributor.id)
                
                from models.user import User
                dist_user = User.query.filter_by(distributor_id=distributor.id).first()
                if dist_user:
                    from services.email_service import email_service
                    email_service.send_new_lead_notification(
                        to_email=dist_user.email,
                        distributor_name=distributor.name,
                        lead_name=f"{first_name} {last_name}",
                        lead_email=email or "",
                        lead_phone=phone or "",
                        source="AI Agent Chat",
                        lang=distributor.language or 'en'
                    )
            except Exception as notify_err:
                logger.warning(f"Lead notification failed (non-blocking): {notify_err}")

            return f"Successfully registered lead: {first_name} {last_name} and linked to the active conversation."
        except Exception as e:
            db.session.rollback()
            return f"Error registering lead: {str(e)}"

    def list_recent_leads(self, limit: int = 10) -> str:
        db.session.rollback()
        distributor = getattr(ctx, 'current_company', None)
        if not distributor:
            return "Error: context missing"
            
        leads = Lead.query.filter_by(distributor_id=distributor.id).order_by(Lead.created_at.desc()).limit(limit).all()
        if not leads:
            return "No leads found."
            
        result = []
        for l in leads:
            result.append(f"- ID: {l.id} | {l.full_name} ({l.status.value}) | Tel: {l.phone}")
            
        return "Recent Leads:\n" + "\n".join(result)

    def get_lead_details(self, lead_id: int = None, email: str = None) -> str:
        db.session.rollback()
        distributor = getattr(ctx, 'current_company', None)
        if not distributor:
            return "Error: context missing"
            
        lead = None
        if lead_id:
            lead = Lead.query.filter_by(id=lead_id, distributor_id=distributor.id).first()
        elif email:
            lead = Lead.query.filter_by(email=email, distributor_id=distributor.id).first()
            
        if not lead:
            return "Lead not found."
            
        # Get status safely (handle both string and Enum)
        status_val = lead.status.value if hasattr(lead.status, 'value') else str(lead.status)
        source_val = lead.source.value if hasattr(lead.source, 'value') else str(lead.source)

        details = [
            f"Details for {lead.full_name}:",
            f"Status: {status_val}",
            f"Email: {lead.email}",
            f"Phone: {lead.phone}",
            f"Source: {source_val}",
            f"Created: {lead.created_at.strftime('%Y-%m-%d')}"
        ]
        
        # Add Wellness Evaluation details if exist
        try:
            # Wellness evaluations relationship is dynamic
            latest_eval = lead.wellness_evaluations.order_by(WellnessEvaluation.created_at.desc()).first()
            if latest_eval:
                details.append(f"\n[WELLNESS EVALUATION]")
                details.append(f"Date: {latest_eval.created_at.strftime('%Y-%m-%d')}")
                details.append(f"Goal: {latest_eval.primary_goal}")
                details.append(f"Diagnosis: {latest_eval.diagnosis}")
                details.append(f"Recommendations: {latest_eval.recommendations}")
                details.append(f"BMI: {latest_eval.bmi}")
        except Exception as e:
            logger.warning(f"Error fetching wellness evaluation for lead {lead.id}: {e}")

        # Add latest note if exists
        try:
            latest_note = lead.note_records.order_by(datetime.utcnow().desc()).first()
            if latest_note:
                details.append(f"\nLatest Note: {latest_note.content}")
        except Exception as e:
            logging.error(f"Error fetching latest note in get_lead_details: {e}")
            
        return "\n".join(details)

    def toggle_ai_response(self, target_type: str, target_id: int, enabled: bool) -> str:
        db.session.rollback()
        distributor = getattr(ctx, 'current_company', None)
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
        db.session.rollback()
        distributor = getattr(ctx, 'current_company', None)
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
