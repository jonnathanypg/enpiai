"""
LangGraph Tools
Wraps existing OnePunch services as LangChain tools for use in LangGraph workflows.

All tools follow the pattern:
1. Import existing service
2. Get company context from state/config
3. Call service method
4. Return result as string
"""
from langchain_core.tools import tool
from typing import Optional
import json


# ============================================================
# RAG / Knowledge Base Tools
# ============================================================

@tool
def consult_knowledge_base(query: str) -> str:
    """
    Search the company knowledge base for relevant information.
    Use this when you need to find information about products, services, policies, or any company-specific data.
    
    Args:
        query: The search query to find information
        
    Returns:
        Relevant information from the knowledge base
    """
    from flask import g
    from services.rag_service import RAGService
    
    try:
        company = getattr(g, 'current_company', None)
        if not company:
            return "Knowledge base not available - no company context"
        
        rag_service = RAGService(company)
        results = rag_service.query(query, top_k=3)
        
        if results:
            texts = [r.get('content', '') for r in results if r.get('content')]
            return "\n---\n".join(texts) if texts else "No relevant information found in knowledge base."
        return "No relevant information found in knowledge base."
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"


# ============================================================
# Customer Verification Tools
# ============================================================

@tool
def lookup_customer(query: str) -> str:
    """
    Search for a registered customer by email, phone, or name.
    Use this to verify identity before processing payments or accessing sensitive info.
    
    Args:
        query: Search term. MUST be provided by the user. Do NOT guess or infer emails not present in chat.
        
    Returns:
        Found customer details or "Customer not found"
    """
    from flask import g
    from services.customer_service import CustomerService
    
    try:
        # Preventive rollback for stale connections
        try:
            from extensions import db
            db.session.rollback()
        except Exception:
            pass
            
        company = getattr(g, 'current_company', None)
        if not company: return "No company context"
        
        results = CustomerService.lookup_by_term(company.id, query)
        if not results:
            return "Customer not found. Please ask for their full name and email to register them."
            
        response = "Found customers:\n"
        for c in results:
            response += f"- ID: {c.id}, Name: {c.first_name} {c.last_name}, Email: {c.email}, IdentNum: {c.ident_number}, Location: {c.city or 'None'}, {c.country or 'None'}\n"
        return response
    except Exception as e:
        from extensions import db
        db.session.rollback()
        return f"Error looking up customer: {str(e)}"
        
@tool
def register_customer(first_name: str, last_name: str, email: str, ident_number: Optional[str] = None, phone: Optional[str] = None, country: Optional[str] = None, city: Optional[str] = None, buying_role: Optional[str] = "End User") -> str:
    """
    Register a new customer or update existing details.
    
    Args:
        first_name: Customer's first name. ASK USER if unknown.
        last_name: Customer's last name. ASK USER if unknown.
        email: Customer's email address. MUST be explicitly provided by user. DO NOT FABRICATE.
        ident_number: Official Identification Number (DNI/Passport). ASK USER.
        phone: Optional phone number
        country: Optional Customer country (for timezones)
        city: Optional Customer city (for timezones)
        buying_role: Role in purchasing process (Default: 'End User'). Options: 'End User', 'Decision Maker', 'Influencer', 'Champion', 'Economic Buyer'.
        
    Returns:
        Registration confirmation with Customer ID
    """
    from flask import g
    from services.customer_service import CustomerService
    from extensions import db
    
    try:
        # Preventive rollback for stale connections
        try:
            db.session.rollback()
        except Exception:
            pass
            
        import pytz
        from datetime import datetime, timedelta
        
        company = getattr(g, 'current_company', None)
        if not company: return "No company context"
        
        data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'ident_number': ident_number,
            'phone': phone,
            'country': country,
            'city': city,
            'buying_role': buying_role
        }
        
        # Check if customer exists to determine if we should set status to NEW
        existing_customer = CustomerService.get_customer(company.id, email, phone)
        is_new = existing_customer is None
        
        customer = CustomerService.upsert_customer(company.id, data)
        
        # Sync to HubSpot immediately
        try:
            from services.hubspot_service import HubSpotService
            hubspot = HubSpotService(company)
            
            # Only set lead_status='NEW' if it's a fresh creation
            hs_status = 'NEW' if is_new else None
            
            hubspot.create_or_update_contact(
                email=customer.email,
                firstname=customer.first_name,
                lastname=customer.last_name,
                phone=customer.phone,
                buying_role=customer.buying_role,
                lead_status=hs_status
            )
        except Exception as hs_e:
            print(f"HubSpot Sync Error: {hs_e}")
            
        return f"Customer registered successfully! ID: {customer.id}, Name: {customer.first_name} {customer.last_name}, Location: {customer.city or 'N/A'}, {customer.country or 'N/A'}"
    except Exception as e:
        db.session.rollback()
        return f"Error registering customer: {str(e)}"

# ============================================================
# Payment Tools
# ============================================================

@tool
def paypal_create_order(amount: float, currency: str = "USD", description: str = "Payment", customer_id: Optional[int] = None) -> str:
    """
    Create a PayPal payment order. 
    PREREQUISITE: You MUST verify the customer identity first using 'lookup_customer' or 'register_customer'.
    
    Args:
        amount: Payment amount (confirmed by customer)
        currency: Currency code (USD, EUR)
        description: Description of service/product
        customer_id: The numeric ID of the verified customer (from lookup/register tool)
        
    Returns:
        Approval URL for the customer to click
    """
    from flask import g
    from services.paypal_toolkit import get_paypal_toolkit
    from services.transaction_service import TransactionService
    
    try:
        # Preventive rollback for stale connections
        try:
            from extensions import db
            db.session.rollback()
        except Exception:
            pass
            
        company = getattr(g, 'current_company', None)
        conversation = getattr(g, 'current_conversation', None) # New context variable
        
        toolkit = get_paypal_toolkit(company)
        
        # 1. Create Transaction Logs (Pending)
        txn = TransactionService.create_transaction(
            company_id=company.id if company else 1,
            amount=amount,
            currency=currency,
            description=description,
            customer_id=customer_id,
            conversation_id=conversation.id if conversation else None,
            provider="paypal",
            channel=conversation.channel if conversation else "webchat"
        )
        
            # 2. Call PayPal API
        # Append transaction ID to description for tracking? Optional.
        
        result = toolkit.create_order(amount, currency, description)
        
        if result.get('success'):
            order_id = result['order_id']
            # 3. Update Transaction with Provider ID
            TransactionService.update_provider_order_id(txn.id, order_id)
            
            # --- HUBSPOT INTEGRATION ---
            try:
                from services.hubspot_service import HubSpotService
                hubspot = HubSpotService(company)
                # Create Deal in HubSpot pipeline (Opportunity Stage)
                # We use the customer's email which we should have if they are registered/looked up.
                # If we passed customer_id to create_order, we can look up the customer model.
                
                customer_email = None
                if customer_id:
                    from models.customer import Customer
                    cust_obj = Customer.query.get(customer_id)
                    if cust_obj: customer_email = cust_obj.email
                
                if customer_email:
                    hubspot.create_pending_payment_deal(
                        contact_email=customer_email,
                        amount=float(amount),
                        description=description,
                        provider_order_id=order_id
                    )
            except Exception as hs_err:
                print(f"HubSpot Sync Error (Create Order): {hs_err}")
            # ---------------------------
            
            # Format the link as Markdown for clean display in chat
            formatted_link = f"[👉 Click aquí para pagar]({result['approval_url']})"
            
                'formatted_link': formatted_link,
                'message': f"¡Link de pago creado! Orden: {order_id}. El cliente debe hacer click en el enlace para completar el pago."
            })
            
            # --- AUTO-RESOLVE CONVERSATION ---
            try:
                from datetime import datetime
                from extensions import db
                conversation = getattr(g, 'current_conversation', None)
                if conversation:
                    conversation.is_resolved = True
                    conversation.resolved_at = datetime.utcnow()
                    db.session.commit()
            except Exception as e:
                print(f"Error auto-resolving conversation: {e}")
            # ---------------------------------
            
            return json.dumps({
                'success': True,
                'order_id': order_id,
                'approval_url': result['approval_url'],
                'formatted_link': formatted_link,
                'message': f"¡Link de pago creado! Orden: {order_id}. El cliente debe hacer click en el enlace para completar el pago."
            })
        else:
            return json.dumps({'success': False, 'error': result.get('error', 'Failed to create order')})
    except Exception as e:
        # Rollback any failed transaction to clean connection
        from extensions import db
        db.session.rollback()
        return json.dumps({'success': False, 'error': str(e)})


@tool
def paypal_capture_order(order_id: str) -> str:
    """
    Capture a PayPal payment after approval.
    """
    from flask import g
    from services.paypal_toolkit import get_paypal_toolkit
    from services.transaction_service import TransactionService
    from models.transaction import TransactionStatus
    
    try:
        company = getattr(g, 'current_company', None)
        toolkit = get_paypal_toolkit(company)
        result = toolkit.capture_order(order_id)
        
        if result.get('success'):
            # Update Transaction Status
            TransactionService.update_status_by_order_id(order_id, TransactionStatus.COMPLETED.value)
            
            # --- HUBSPOT INTEGRATION ---
            try:
                from services.hubspot_service import HubSpotService
                # We need company context. It's in 'g'
                hubspot = HubSpotService(company)
                
                # We need to find the specific deal to close it. 
                # Strategy: Search deal by order_id in description or attempt to match amount/contact.
                # For now, let's update the CONTACT lifecycle to Customer.
                
                # Retrieve transaction to get customer
                from models.transaction import Transaction
                txn = Transaction.query.filter_by(provider_order_id=order_id).first()
                if txn and txn.customer and txn.customer.email:
                    # Update Contact to 'customer'
                    hubspot.create_or_update_contact(
                        email=txn.customer.email, 
                        properties={'lifecyclestage': 'customer'}
                    )
                    
                    # Ideally we would find the deal and close it as 'closedwon'.
                    # We can try search_deals using the hubspot service logic if we implement it there?
                    # For now, updating lifecycle is the MVP critical step.
            except Exception as hs_err:
                 print(f"HubSpot Sync Error (Capture Order): {hs_err}")
            except Exception as hs_err:
                 print(f"HubSpot Sync Error (Capture Order): {hs_err}")
            # ---------------------------

            # --- AUTO-RESOLVE CONVERSATION ---
            try:
                conversation = getattr(g, 'current_conversation', None)
                if conversation:
                    from datetime import datetime
                    from extensions import db
                    conversation.is_resolved = True
                    conversation.resolved_at = datetime.utcnow()
                    db.session.commit()
            except Exception as e:
                print(f"Error auto-resolving conversation: {e}")
            # ---------------------------------
            
            return json.dumps({
                'success': True,
                'message': 'Payment captured and verified!',
                'capture_id': result.get('capture_id')
            })
        else:
            return json.dumps({'success': False, 'error': result.get('error', 'Capture failed')})
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


@tool
def paypal_get_order(order_id: str) -> str:
    """
    Get the status of a PayPal order.
    """
    from flask import g
    from services.paypal_toolkit import get_paypal_toolkit
    
    try:
        company = getattr(g, 'current_company', None)
        toolkit = get_paypal_toolkit(company)
        result = toolkit.get_order(order_id)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


# ============================================================
# Communication Tools
# ============================================================

@tool
def send_whatsapp(to: str, message: str) -> str:
    """
    Send a WhatsApp message to a phone number.
    
    Args:
        to: Phone number with country code (e.g., +1234567890)
        message: Message content to send
        
    Returns:
        Confirmation of message sent
    """
    from flask import g
    from services.twilio_service import TwilioService
    
    try:
        company = getattr(g, 'current_company', None)
        if not company:
            return "Cannot send WhatsApp - no company context"
        
        twilio = TwilioService(company)
        result = twilio.send_whatsapp(to, message)
        
        if result.get('success'):
            return f"WhatsApp message sent successfully to {to}"
        else:
            return f"Failed to send WhatsApp: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"Error sending WhatsApp: {str(e)}"


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """
    Send an email to a recipient.
    
    Args:
        to: Email address of recipient
        subject: Email subject line
        body: Email body content (supports Markdown formatting: **bold**, - bullets, ## headers)
        
    Returns:
        Confirmation of email sent
    """
    from flask import g

    from services.email_service import EmailService
    import re
    from extensions import db
    from datetime import datetime
    
    def markdown_to_html(text: str) -> str:
        """Convert basic Markdown to HTML for email formatting."""
        # Convert headers
        text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
        
        # Convert bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        
        # Convert italic
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        
        # Convert bullet points
        text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        text = re.sub(r'(<li>.+</li>\n?)+', r'<ul>\g<0></ul>', text)
        
        # Convert line breaks to <br> (preserve paragraph structure)
        text = re.sub(r'\n\n', r'</p><p>', text)
        text = re.sub(r'\n', r'<br>', text)
        
        # Wrap in paragraph
        text = f'<p>{text}</p>'
        
        # Clean up empty paragraphs
        text = text.replace('<p></p>', '')
        
        return text
    
    try:
        # Preventive rollback for stale connections before accessing company context
        try:
            from extensions import db
            db.session.rollback()
        except Exception:
            pass
            
        company = getattr(g, 'current_company', None)
        if not company:
            return "Cannot send email - no company context"
        
        # Convert Markdown body to HTML for professional formatting
        html_body = markdown_to_html(body)
        
        result = EmailService.send_email(
            company_id=company.id,
            to_email=to,
            subject=subject,
            body=html_body
        )
        
        if result.get('success'):
            # --- LOG EMAIL ---
            try:
                from models.email_log import EmailLog
                # Helper to get conversation/customer context
                conversation = getattr(g, 'current_conversation', None)
                customer = getattr(g, 'current_customer', None) # If available
                
                log = EmailLog(
                    company_id=company.id,
                    conversation_id=conversation.id if conversation else None,
                    customer_id=customer.id if customer else None,
                    to_email=to,
                    subject=subject,
                    body_summary=body[:500] + ('...' if len(body) > 500 else '')
                )
                db.session.add(log)
                db.session.commit()
            except Exception as e_log:
                print(f"Error logging email: {e_log}")
            # -----------------
            
            # --- AUTO-RESOLVE CONVERSATION ---
            try:
                conversation = getattr(g, 'current_conversation', None)
                if conversation:
                    conversation.is_resolved = True
                    conversation.resolved_at = datetime.utcnow()
                    db.session.commit()
            except Exception as e:
                print(f"Error auto-resolving conversation: {e}")
            # ---------------------------------
            return f"Email sent successfully to {to}"
        else:
            return f"Failed to send email: {result.get('error', 'Unknown error')}"
    except Exception as e:
        # Rollback on error to ensure clean state for next tool
        try:
            from extensions import db
            db.session.rollback()
        except Exception:
            pass
        return f"Error sending email: {str(e)}"


@tool
def make_call(to: str, purpose: str) -> str:
    """
    Initiate a voice call to a phone number.
    
    Args:
        to: Phone number to call (with country code)
        purpose: Brief description of the call purpose
        
    Returns:
        Call initiation status
    """
    from flask import g
    from services.livekit_service import LiveKitService
    
    try:
        company = getattr(g, 'current_company', None)
        if not company:
            return "Cannot make call - no company context"
        
        livekit = LiveKitService(company)
        result = livekit.initiate_outbound_call(to, purpose)
        
        if result.get('success'):
            return f"Call initiated to {to} for: {purpose}"
        else:
            return f"Failed to initiate call: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"Error initiating call: {str(e)}"


# ============================================================
# Calendar Tools
# ============================================================

@tool
def schedule_appointment(
    date: str, 
    time: str, 
    attendee_email: str, 
    client_name: str = "",
    meeting_reason: str = "",
    client_city: str = "",
    client_country: str = "",
    client_timezone: str = ""
) -> str:
    """
    Schedule an appointment on Google Calendar with Google Meet link.
    IMPORTANT: Collect city/country/timezone and meeting reason BEFORE calling.
    
    Args:
        date: Date in YYYY-MM-DD format (Client's date if timezone provided, else Company's)
        time: Time in HH:MM format (Client's time if timezone provided, else Company's)
        attendee_email: Email of the person to invite
        client_name: Client's full name (lookup by email if empty)
        meeting_reason: Purpose/subject of the meeting
        client_city: Client's city
        client_country: Client's country
        client_timezone: Client's IANA timezone (e.g. "America/Buenos_Aires"). IF PROVIDED, time is treated as local to this zone.
        
    Returns:
        Appointment confirmation with Google Meet link
    """
    from flask import g
    from services.google_service import GoogleCalendarIntegration
    from models.appointment import Appointment, AppointmentStatus
    from models.customer import Customer
    from extensions import db
    from datetime import datetime, timedelta
    import pytz
    
    try:
        company = getattr(g, 'current_company', None)
        conversation = getattr(g, 'current_conversation', None)
        if not company:
            return "Cannot schedule - no company context"
        
        # 1. Resolve Customer Name
        customer = None
        if attendee_email:
            customer = Customer.query.filter_by(company_id=company.id, email=attendee_email).first()
        
        if not client_name and customer:
            client_name = f"{customer.first_name} {customer.last_name}".strip()
            
        # 2. Build Title and Description
        title = f"Reunión con {client_name} | {company.name}" if client_name else f"Reunión | {company.name}"
        
        description_parts = []
        if meeting_reason: description_parts.append(f"Asunto: {meeting_reason}")
        if client_timezone: description_parts.append(f"Zona horaria cliente: {client_timezone}")
        loc_str = ", ".join(filter(None, [client_city, client_country]))
        if loc_str: description_parts.append(f"Ubicación cliente: {loc_str}")
        if attendee_email: description_parts.append(f"Email: {attendee_email}")
        description = "\n".join(description_parts)
        
        # 3. Timezone Logic - The Critical Fix
        company_tz_str = company.timezone or 'UTC'
        company_tz = pytz.timezone(company_tz_str)
        
        # Parse naive datetime from arguments
        naive_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        
        if client_timezone:
            try:
                # If client timezone is provided, localize to THAT zone
                client_tz = pytz.timezone(client_timezone)
                localized_dt = client_tz.localize(naive_dt)
                # Convert to UTC for storage and API
                final_dt = localized_dt.astimezone(pytz.UTC)
                print(f"[DEBUG] Converted {naive_dt} ({client_timezone}) -> {final_dt} (UTC)")
            except Exception as e:
                return f"Error con la zona horaria del cliente '{client_timezone}': {str(e)}"
        else:
            # Fallback: Assume the time is in Company's Timezone
            localized_dt = company_tz.localize(naive_dt)
            final_dt = localized_dt.astimezone(pytz.UTC)
            print(f"[DEBUG] Assumed Company Time: {naive_dt} ({company_tz_str}) -> {final_dt} (UTC)")

        if client_timezone:
            # Add note about converted time if different
            description += f"\n\n(Time converted from customer's {client_timezone} timezone)"

        # 4. Schedule on Google Calendar
        calendar = GoogleCalendarIntegration(company=company)
        result = calendar.schedule_meeting(
            title=title,
            start_time=final_dt,
            duration_minutes=30,
            description=description,
            attendees=[attendee_email]
        )
        
        if result.get('success'):
            meet_link = result.get('meet_link', 'No link generated')
            google_event_id = result.get('event_id', '')
            
            # 5. Save to Database
            appointment = Appointment(
                company_id=company.id,
                customer_id=customer.id if customer else None,
                conversation_id=conversation.id if conversation else None,
                title=title,
                description=description,
                start_time=final_dt, # Store as UTC
                end_time=final_dt + timedelta(minutes=30),
                duration_minutes=30,
                client_city=client_city,
                client_country=client_country,
                client_timezone=client_timezone,
                google_event_id=google_event_id,
                google_meet_link=meet_link,
                status=AppointmentStatus.SCHEDULED.value,
                channel_type=conversation.channel if conversation else 'webchat'
            )
            db.session.add(appointment)
            
            # --- AUTO-RESOLVE CONVERSATION ---
            if conversation:
                conversation.is_resolved = True
                conversation.resolved_at = datetime.utcnow()
            # ---------------------------------
                
            db.session.commit()
            
            # 6. HubSpot Sync (Lifecycle -> SQL)
            try:
                if attendee_email:
                    from services.hubspot_service import HubSpotService
                    hubspot = HubSpotService(company)
                    # Mark as SQL (Sales Qualified Lead)
                    hubspot.mark_as_scheduled(attendee_email)
            except Exception as hs_err:
                print(f"HubSpot Sync Error (Schedule Appointment): {hs_err}")
            # ---------------------------
            
            response = f"✅ Cita agendada: {title}\n📅 {date} a las {time} ({client_timezone or company_tz_str})"
            if meet_link: response += f"\n🔗 Google Meet: {meet_link}"
            response += f"\n📧 Invitación enviada a: {attendee_email}"
            return response
        else:
            return f"Error al agendar en Google Calendar: {result.get('error', 'Desconocido')}"

    except Exception as e:
        from extensions import db
        db.session.rollback()
        return f"Error scheduling appointment: {str(e)}"


@tool
def check_availability(date: str, client_timezone: str = None, preferred_time: str = None) -> str:
    """
    Check available slots for a given date.
    Args:
        date: YYYY-MM-DD format
        client_timezone: Client's IANA timezone (e.g. 'America/Buenos_Aires')
        preferred_time: Optional HH:MM format. If provided and unavailable, returns 2 slots before and 2 after.
    """
    from services.google_service import GoogleCalendarIntegration
    from flask import g
    import pytz
    from datetime import datetime, timedelta
    
    try:
        company = getattr(g, 'current_company', None)
        if not company:
            return "Cannot check availability - no company context"
        
        calendar = GoogleCalendarIntegration(company)
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return "Invalid date format. Use YYYY-MM-DD"
            
        slots = calendar.get_free_slots(date_obj)
        
        if not slots:
            return f"No hay disponibilidad para el {date}"

        # Setup timezone conversion
        company_tz = pytz.timezone(company.timezone) if company.timezone else pytz.UTC
        target_tz = pytz.timezone(client_timezone) if client_timezone else company_tz
        tz_label = f"({client_timezone})" if client_timezone else "(Hora Empresa)"
        
        # Convert all slots to target timezone for comparison
        converted_slots = []
        for s in slots:
            start_local = s['start'].astimezone(target_tz)
            end_local = s['end'].astimezone(target_tz)
            converted_slots.append({
                'start': start_local,
                'end': end_local,
                'str': f"{start_local.strftime('%H:%M')}-{end_local.strftime('%H:%M')}"
            })
        
        # If preferred_time is provided, check if available and suggest alternatives
        if preferred_time:
            try:
                pref_hour, pref_min = map(int, preferred_time.split(':'))
                pref_dt = target_tz.localize(datetime.combine(date_obj, datetime.min.time().replace(hour=pref_hour, minute=pref_min)))
                
                # Check if preferred time is available
                is_available = any(s['start'] <= pref_dt < s['end'] for s in converted_slots)
                
                if is_available:
                    return f"✅ El horario {preferred_time} está disponible el {date} {tz_label}"
                else:
                    # Find 2 slots before and 2 after the preferred time
                    before = [s for s in converted_slots if s['start'] < pref_dt][-2:]  # Last 2 before
                    after = [s for s in converted_slots if s['start'] >= pref_dt][:2]   # First 2 after
                    
                    suggestions = before + after
                    if not suggestions:
                        return f"No hay horarios cercanos a {preferred_time} disponibles el {date}"
                    
                    suggestion_strs = [s['str'] for s in suggestions]
                    return f"❌ El horario {preferred_time} no está disponible. Opciones cercanas {tz_label}: {', '.join(suggestion_strs)}"
                    
            except (ValueError, AttributeError):
                pass  # Invalid preferred_time format, fall through to show all
        
        # Default: show all available slots
        all_slots_str = ", ".join([s['str'] for s in converted_slots])
        return f"Horarios disponibles el {date} {tz_label}: {all_slots_str}"
            
    except Exception as e:
        return f"Error checking availability: {str(e)}"


# ============================================================
# CRM Tools (HubSpot)
# ============================================================

@tool
def hubspot_create_contact(email: str, name: str, phone: Optional[str] = None) -> str:
    """
    Create or update a contact in HubSpot CRM.
    
    Args:
        email: Contact email address
        name: Contact full name
        phone: Optional phone number
        
    Returns:
        Contact creation/update confirmation
    """
    from flask import g
    from integrations.hubspot import HubSpotIntegration
    
    try:
        company = getattr(g, 'current_company', None)
        if not company:
            return "Cannot create contact - no company context"
        
        hubspot = HubSpotIntegration(company)
        
        # Split name
        parts = name.strip().split(' ', 1)
        firstname = parts[0]
        lastname = parts[1] if len(parts) > 1 else ""
        
        result = hubspot.create_or_update_contact(
            email=email, 
            firstname=firstname, 
            lastname=lastname, 
            phone=phone
        )
        
        if result.get('success'):
            return f"Contact created/updated: {name} ({email})"
        else:
            return f"Failed to create contact: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"Error creating contact: {str(e)}"


@tool
def hubspot_create_deal(contact_email: str, deal_name: str, amount: float, stage: str = "appointmentscheduled") -> str:
    """
    Create a deal/opportunity in HubSpot CRM.
    
    Args:
        contact_email: Email of associated contact
        deal_name: Name of the deal
        amount: Deal value amount
        stage: Deal stage (default: appointmentscheduled)
        
    Returns:
        Deal creation confirmation
    """
    from flask import g
    from integrations.hubspot import HubSpotIntegration
    
    try:
        company = getattr(g, 'current_company', None)
        if not company:
            return "Cannot create deal - no company context"
        
        hubspot = HubSpotIntegration(company)
        result = hubspot.create_deal(contact_email, deal_name, amount, stage)
        
        if result.get('success'):
            return f"Deal created: {deal_name} (${amount})"
        else:
            return f"Failed to create deal: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"Error creating deal: {str(e)}"


# ============================================================
# Tool Registry
# ============================================================

def get_tools_for_agent(agent, company, enabled_features=None):
    """
    Get list of tools available for an agent based on enabled features.
    
    Args:
        agent: Agent model instance (can be None if enabled_features is provided)
        company: Company model instance
        enabled_features: Optional list of enabled feature names (strings).
                         If not provided, will query agent.features (legacy fallback).
        
    Returns:
        List of tool functions
    """
    tools = []
    
    # Get enabled feature names
    if enabled_features is None:
        # Legacy fallback: query from agent object
        # This can fail if session is stale, so prefer passing enabled_features explicitly
        enabled_features = [f.name for f in agent.features.filter_by(is_enabled=True).all()]
    
    
    # Check for calendar capability
    calendar_enabled = any(f in enabled_features for f in ['calendar_integration', 'calendar', 'schedule_meeting'])
    
    # RAG is ALWAYS available - it's fundamental for answering company questions
    # Agents should always be able to consult the knowledge base
    tools.append(consult_knowledge_base)
    
    # Customer management tools - needed for payments, calendar AND email
    # (for identity verification and data collection in any interaction flow)
    if 'process_payment' in enabled_features or calendar_enabled or 'send_email' in enabled_features:
        if lookup_customer not in tools:
            tools.append(lookup_customer)
        if register_customer not in tools:
            tools.append(register_customer)
    
    # Payment tools
    if 'process_payment' in enabled_features:
        tools.extend([
            paypal_create_order, 
            paypal_capture_order, 
            paypal_get_order
        ])
    
    # Communication tools
    if 'send_whatsapp' in enabled_features:
        tools.append(send_whatsapp)
    
    # Email - available ONLY if explicitly enabled (usable by any flow that needs it)
    if 'send_email' in enabled_features:
        tools.append(send_email)
    
    if 'voice_calls' in enabled_features:
        tools.append(make_call)
    
    # Calendar tools
    if calendar_enabled:
        tools.extend([schedule_appointment, check_availability])
    
    # CRM tools
    if 'crm_integration' in enabled_features:
        tools.extend([hubspot_create_contact, hubspot_create_deal])
    
    return tools


# Export all tools for inspection
ALL_TOOLS = [
    consult_knowledge_base,
    paypal_create_order,
    paypal_capture_order,
    paypal_get_order,
    lookup_customer,    # Added
    register_customer,  # Added
    send_whatsapp,
    send_email,
    make_call,
    schedule_appointment,
    check_availability,
    hubspot_create_contact,
    hubspot_create_deal
]
