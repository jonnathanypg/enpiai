"""
LangGraph Tools Definition
Wraps core services into LangChain-compatible tools for use by the agent.
"""
import json
import logging
from typing import List, Optional
from langchain_core.tools import tool
from flask import g

# Import services
from services.rag_service import rag_service
from services.google_service import google_service
from services.email_service import email_service
from services.pdf_service import pdf_service
from models.lead import Lead, LeadStatus
from models.customer import Customer
from models.appointment import Appointment
from models.wellness_evaluation import WellnessEvaluation
from extensions import db

logger = logging.getLogger(__name__)


# ==============================================================================
# RAG / Knowledge Base Tools
# ==============================================================================

@tool
def consult_knowledge_base(query: str) -> str:
    """
    Consults the company's internal knowledge base (PDFs, docs) to answer questions
    about services, products, prices, or company info.
    
    Args:
        query: The specific question or search term.
        
    Returns:
        String with relevant information found.
    """
    distributor = getattr(g, 'current_company', None)
    if not distributor:
        return "Error: No distributor context found."
        
    logger.info(f"Tool: consult_knowledge_base query='{query}' dist={distributor.id}")
    
    results = rag_service.query(query, distributor.id, top_k=3)
    
    if not results:
        return "No information found in the knowledge base."
        
    # Format results
    context_text = "\n\n".join([r['text'] for r in results])
    return f"Information from knowledge base:\n{context_text}"


@tool
def wellness_evaluation_link() -> str:
    """
    Returns the link for the public wellness evaluation form.
    Use this when a user wants to start a health assessment.
    """
    distributor = getattr(g, 'current_company', None)
    if not distributor:
        return "Error: No distributor context found."
        
    # TODO: Replace with actual frontend URL
    url = f"https://platform.enpiai.com/wellness/{distributor.id}"
    return f"Here is the link for your wellness evaluation: {url}"


# ==============================================================================
# CRM / Customer Tools
# ==============================================================================

@tool
def lookup_customer(email: str) -> str:
    """
    Look up a customer or lead by email. 
    Use this to verify identity before scheduling or payments.
    
    Args:
        email: The user's email address.
    """
    distributor = getattr(g, 'current_company', None)
    if not distributor:
        return "Error: context missing"
        
    # Check Customer first
    customer = Customer.query.filter_by(distributor_id=distributor.id, email=email).first()
    if customer:
        return json.dumps({
            "status": "found",
            "type": "customer",
            "name": f"{customer.first_name} {customer.last_name}",
            "id": customer.id
        })
        
    # Check Lead
    lead = Lead.query.filter_by(distributor_id=distributor.id, email=email).first()
    if lead:
        return json.dumps({
            "status": "found",
            "type": "lead",
            "name": f"{lead.first_name} {lead.last_name}",
            "id": lead.id
        })
        
    return json.dumps({"status": "not_found", "message": "User not found in records."})


@tool
def register_lead(first_name: str, last_name: str, email: str, phone: str = None) -> str:
    """
    Register a new prospect/lead in the system.
    
    Args:
        first_name: Customer's first name
        last_name: Customer's last name
        email: Customer's email
        phone: (Optional) Customer's phone
    """
    distributor = getattr(g, 'current_company', None)
    if not distributor:
        return "Error: context missing"
        
    try:
        # Check if exists
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

        # Notify distributor about new lead
        try:
            from models.user import User
            dist_user = User.query.filter_by(distributor_id=distributor.id).first()
            if dist_user:
                email_service.send_new_lead_notification(
                    to_email=dist_user.email,
                    distributor_name=distributor.name,
                    lead_name=f"{first_name} {last_name}",
                    lead_email=email or "",
                    lead_phone=phone or "",
                    source="AI Agent Chat",
                    lang=distributor.language or 'en'
                )
        except Exception as mail_err:
            logger.warning(f"Lead notification email failed (non-blocking): {mail_err}")

        return f"Successfully registered lead: {first_name} {last_name}"
    except Exception as e:
        db.session.rollback()
        return f"Error registering lead: {str(e)}"


# ==============================================================================
# Calendar Tools
# ==============================================================================

@tool
def check_availability(date: str, preferred_time: str = None) -> str:
    """
    Check calendar availability for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format.
        preferred_time: Optional preferred time (e.g. "14:00")
    """
    distributor = getattr(g, 'current_company', None)
    if not distributor:
        return "Error: context missing"
        
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


@tool
def schedule_appointment(date: str, time: str, email: str, topic: str) -> str:
    """
    Schedule a meeting on Google Calendar.
    ONLY execute this after the user has explicitly confirmed the time.
    
    Args:
        date: YYYY-MM-DD
        time: HH:MM (24h format)
        email: User's email for invite
        topic: Reason for meeting
    """
    distributor = getattr(g, 'current_company', None)
    if not distributor:
        return "Error: context missing"
        
    try:
        start_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return "Invalid date/time format. Use YYYY-MM-DD and HH:MM."
        
    result = google_service.create_event(
        distributor=distributor,
        title=f"Reunión con {email}: {topic}",
        start_datetime=start_datetime,
        duration_minutes=30,
        description=f"Agendado vía AI Agent.\nTema: {topic}",
        attendee_email=email,
        timezone=distributor.timezone or 'America/Guayaquil'
    )
    
    if 'error' in result:
        return f"Failed to schedule: {result['error']}"
        
    # Save to local DB
    # Find lead/customer ID
    lead = Lead.query.filter_by(distributor_id=distributor.id, email=email).first()
    customer = Customer.query.filter_by(distributor_id=distributor.id, email=email).first()
    
    appt = Appointment(
        distributor_id=distributor.id,
        title=topic,
        start_time=start_datetime,
        end_time=start_datetime + timedelta(minutes=30),
        status='scheduled',
        google_event_id=result.get('event_id'),
        lead_id=lead.id if lead else None,
        customer_id=customer.id if customer else None
    )
    db.session.add(appt)
    db.session.commit()
    
    return f"Cita agendada exitosamente para el {date} a las {time}. Link: {result.get('html_link')}"


# ==============================================================================
# Communication Tools
# ==============================================================================

@tool
def send_email(to_email: str, subject: str, content: str) -> str:
    """
    Send an email to a user.
    Use this to send summaries, receipts, or requested info.
    
    Args:
        to_email: Recipient email
        subject: Email subject
        content: HTML content of the email
    """
    distributor = getattr(g, 'current_company', None)
    
    # Check if this distributor has specific email settings
    from_email = distributor.contact_email if distributor else None
    
    success = email_service.send(to_email, subject, content, from_email=from_email)
    
    if success:
        return f"Email sent successfully to {to_email}."
    else:
        return "Failed to send email. Detailed logs checked."


# ==============================================================================
# Tool Registry
# ==============================================================================

def get_tools_for_agent(agent, distributor, enabled_features: List[str] = None) -> List:
    """
    Return list of tools available to this agent based on enabled features.
    
    Args:
        agent: Agent model instance
        distributor: Distributor model instance
        enabled_features: List of feature names strings
    """
    tools = []
    
    # Default feature list if not provided
    if enabled_features is None:
        enabled_features = [f.name for f in agent.features.filter_by(is_enabled=True).all()]
        
    # 1. Knowledge Base (RAG)
    if 'knowledge_base' in enabled_features or 'rag' in enabled_features:
        tools.append(consult_knowledge_base)
        
    # 2. CRM / Identity
    if 'crm_integration' in enabled_features or 'lead_capture' in enabled_features:
        tools.append(lookup_customer)
        tools.append(register_lead)
        
    # 3. Calendar
    if 'calendar_integration' in enabled_features or 'schedule_meeting' in enabled_features:
        tools.append(check_availability)
        tools.append(schedule_appointment)
        
    # 4. Email
    if 'email_integration' in enabled_features:
        tools.append(send_email)
        
    # 5. Wellness
    if 'wellness_evaluation' in enabled_features:
        tools.append(wellness_evaluation_link)
        
    return tools
