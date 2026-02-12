"""
Analytics & Dashboard Routes
"""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from extensions import db
from models.user import User
from models.conversation import Conversation, Message, ConversationType, MessageChannel
from models.channel import Channel, ChannelStatus
from models.document import Document, DocumentStatus
from models.employee import Employee
from models.customer import Customer

analytics_bp = Blueprint('analytics', __name__)


def get_user_company():
    """Helper to get current user's company"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or not user.company:
            print(f"DEBUG: Analytics - User/Company missing for ID {user_id}")
            return None
        return user.company
    except Exception as e:
        print(f"DEBUG: Analytics - Error: {e}")
        return None


@analytics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Get main dashboard data"""
    company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    # Time ranges
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)
    
    # Conversation stats
    total_conversations = Conversation.query.filter_by(company_id=company.id).count()
    active_conversations = Conversation.query.filter_by(company_id=company.id, is_active=True).count()
    today_conversations = Conversation.query.filter(
        Conversation.company_id == company.id,
        Conversation.started_at >= today_start
    ).count()
    
    # Message stats
    total_messages = db.session.query(func.count(Message.id)).join(Conversation).filter(
        Conversation.company_id == company.id
    ).scalar() or 0
    
    today_messages = db.session.query(func.count(Message.id)).join(Conversation).filter(
        Conversation.company_id == company.id,
        Message.created_at >= today_start
    ).scalar() or 0
    
    # Channel status
    channels = Channel.query.filter_by(company_id=company.id).all()
    connected_channels = sum(1 for c in channels if c.status == ChannelStatus.CONNECTED)
    
    # Document stats
    total_documents = Document.query.filter_by(company_id=company.id).count()
    indexed_documents = Document.query.filter_by(company_id=company.id, status=DocumentStatus.INDEXED).count()
    
    # Employee count
    employee_count = Employee.query.filter_by(company_id=company.id, is_active=True).count()
    
    # Agent stats
    from models.agent import Agent
    agents = Agent.query.filter_by(company_id=company.id).all()
    
    # Integration status (from company.api_keys)
    api_keys = company.api_keys or {}
    integrations = {
        'google_calendar': {
            'connected': bool(api_keys.get('google_oauth_credentials') and api_keys.get('google_calendar_id')),
            'calendar_id': api_keys.get('google_calendar_id')
        },
        'google_sheets': {
            'connected': bool(api_keys.get('google_oauth_credentials') and api_keys.get('google_sheet_id')),
            'sheet_id': api_keys.get('google_sheet_id')
        },
        'hubspot': {
            'connected': bool(api_keys.get('hubspot_access_token')),
            'portal_id': api_keys.get('hubspot_portal_id')
        }
    }
    
    return jsonify({
        'overview': {
            'total_conversations': total_conversations,
            'active_conversations': active_conversations,
            'today_conversations': today_conversations,
            'total_messages': total_messages,
            'today_messages': today_messages
        },
        'channels': {
            'total': len(channels),
            'connected': connected_channels,
            'list': [c.to_dict() for c in channels]
        },
        'documents': {
            'total': total_documents,
            'indexed': indexed_documents
        },
        'team': {
            'employees': employee_count
        },
        'agents': {
            'total': len(agents),
            'list': [{'id': a.id, 'name': a.name, 'status': 'active' if a.is_active else 'inactive'} for a in agents]
        },
        'integrations': integrations
    })


@analytics_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary_stats():
    """Get summary statistics for Overview dashboard"""
    company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    # Time ranges
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Appointments in period
    from models.appointment import Appointment
    appointments_count = Appointment.query.filter(
        Appointment.company_id == company.id,
        Appointment.created_at >= start_date
    ).count()
    
    # Total Revenue (Completed Transactions)
    from models.transaction import Transaction, TransactionStatus
    total_revenue = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.company_id == company.id,
        Transaction.status == TransactionStatus.COMPLETED.value,
        Transaction.created_at >= start_date
    ).scalar() or 0
    
    return jsonify({
        'appointments': appointments_count,
        'total_revenue': round(float(total_revenue), 2),
        'period_days': days
    })



@analytics_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversation_stats():
    """Get detailed conversation statistics"""
    company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    # Parse date range
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Daily conversation count
    daily_stats = db.session.query(
        func.date(Conversation.started_at).label('date'),
        func.count(Conversation.id).label('count')
    ).filter(
        Conversation.company_id == company.id,
        Conversation.started_at >= start_date
    ).group_by(
        func.date(Conversation.started_at)
    ).all()
    
    # Channel breakdown
    channel_stats = db.session.query(
        Conversation.channel,
        func.count(Conversation.id).label('count')
    ).filter(
        Conversation.company_id == company.id,
        Conversation.started_at >= start_date
    ).group_by(Conversation.channel).all()
    
    # Type breakdown (customer vs admin)
    type_stats = db.session.query(
        Conversation.type,
        func.count(Conversation.id).label('count')
    ).filter(
        Conversation.company_id == company.id,
        Conversation.started_at >= start_date
    ).group_by(Conversation.type).all()
    
    # Resolution rate (Action Based)
    from models.transaction import Transaction
    from models.appointment import Appointment
    from models.email_log import EmailLog
    
    all_txns = Transaction.query.filter(Transaction.company_id == company.id, Transaction.created_at >= start_date).count()
    all_appts = Appointment.query.filter(Appointment.company_id == company.id, Appointment.created_at >= start_date).count()
    email_cnt = EmailLog.query.filter(EmailLog.company_id == company.id, EmailLog.sent_at >= start_date).count()
    
    total = Conversation.query.filter(
        Conversation.company_id == company.id,
        Conversation.started_at >= start_date
    ).count()

    resolution_actions = all_txns + all_appts + email_cnt
    
    resolution_rate = (resolution_actions / total * 100) if total > 0 else 0
    
    return jsonify({
        'daily': [{'date': str(d.date), 'count': d.count} for d in daily_stats],
        'by_channel': [{'channel': c.channel if isinstance(c.channel, str) else c.channel.value, 'count': c.count} for c in channel_stats],
        'by_type': [{'type': t.type.value if hasattr(t.type, 'value') else t.type, 'count': t.count} for t in type_stats],
        'resolution_rate': round(resolution_rate, 2),
        'period_days': days
    })


@analytics_bp.route('/funnel', methods=['GET'])
@jwt_required()
def get_funnel_data():
    """Get sales funnel data"""
    company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    # Parse date range
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 1. Total Leads (All Conversations)
    total_leads = Conversation.query.filter(
        Conversation.company_id == company.id,
        Conversation.type == ConversationType.CUSTOMER,
        Conversation.started_at >= start_date
    ).count()
    
    # 2. Awareness (Engaged: > 2 messages OR lead_score > 10)
    # Refined: Conversations with > 1 message (User replied at least once)
    awareness = Conversation.query.filter(
        Conversation.company_id == company.id,
        Conversation.type == ConversationType.CUSTOMER,
        Conversation.started_at >= start_date
    ).join(Message).group_by(Conversation.id).having(func.count(Message.id) >= 2).count()
    
    # 3. Interest (Highly Engaged: lead_score >= 30 OR > 5 messages)
    interest = Conversation.query.filter(
        Conversation.company_id == company.id,
        Conversation.type == ConversationType.CUSTOMER,
        Conversation.started_at >= start_date
    ).join(Message).group_by(Conversation.id).having(
        (func.count(Message.id) >= 5) | (Conversation.lead_score >= 25)
    ).count()
    
    # 4. Consideration (Scheduled Appointment OR Evaluation)
    from models.appointment import Appointment
    consideration = Appointment.query.filter(
        Appointment.company_id == company.id,
        Appointment.created_at >= start_date
    ).count()
    
    # Avoid showing more appointments than leads (though possible if multiple apts per lead)
    # consideration = min(consideration, interest) # Optional capping
    
    # 5. Intent (Pending Transactions / Payment Links)
    from models.transaction import Transaction, TransactionStatus
    intent = Transaction.query.filter(
        Transaction.company_id == company.id,
        Transaction.created_at >= start_date
    ).count()
    
    # 6. Converted (Completed Transactions)
    converted = Transaction.query.filter(
        Transaction.company_id == company.id,
        Transaction.status == TransactionStatus.COMPLETED.value,
        Transaction.created_at >= start_date
    ).count()
    
    # 6. Converted Logic (Union of Sales & Appointments)
    # We want unique conversations that have EITHER a Completed Transaction OR an Appointment
    # Explicitly using a Union query or Python set arithmetic
    
    # --- ACTION-BASED METRICS (User Request) ---
    # Resolution Rate = (All Transactions + All Appointments + All Emails) / Total Leads
    # Conversion Rate = (Completed Transactions + Appointments) / Total Leads
    
    # 1. Count All Transactions (Resolution)
    all_txns_count = Transaction.query.filter(
        Transaction.company_id == company.id,
        Transaction.created_at >= start_date
    ).count()
    
    # 2. Count Completed Transactions (Conversion)
    completed_txns_count = Transaction.query.filter(
        Transaction.company_id == company.id,
        Transaction.created_at >= start_date,
        Transaction.status == TransactionStatus.COMPLETED.value
    ).count()

    # 3. Count Appointments (Both Resolution & Conversion - assuming Scheduling is a conversion)
    # Note: User might want Completed Appts only for conversion? "agendas completadas".
    # Assuming all created appointments in range count as "scheduled". Ideally check status='completed'.
    # For now, counting ALL Appointment records (Creation of agenda). 
    all_appts_count = Appointment.query.filter(
        Appointment.company_id == company.id,
        Appointment.created_at >= start_date
    ).count()

    # 4. Count Emails (Resolution Only)
    from models.email_log import EmailLog
    email_count = EmailLog.query.filter(
        EmailLog.company_id == company.id,
        EmailLog.sent_at >= start_date
    ).count()
    
    # Calculcations
    resolution_actions = all_txns_count + all_appts_count + email_count
    conversion_actions = completed_txns_count + all_appts_count # User said "agendas y pagos", implied creation of agenda is success.

    return jsonify({
        'funnel': [
            {'stage': 'Total Leads', 'count': total_leads},
            {'stage': 'Awareness', 'count': awareness},
            {'stage': 'Interest', 'count': interest},
            {'stage': 'Consideration (Meetings)', 'count': consideration},
            {'stage': 'Intent (Payment Links)', 'count': intent},
            {'stage': 'Converted (Sales)', 'count': converted}
        ],

        # Rate = (Actions / Leads) * 100
        'conversion_rate': round((conversion_actions / total_leads * 100), 2) if total_leads > 0 else 0,
        'resolution_rate': round((resolution_actions / total_leads * 100), 2) if total_leads > 0 else 0,
        'period_days': days
    })


@analytics_bp.route('/sentiment', methods=['GET'])
@jwt_required()
def get_sentiment_data():
    """Get sentiment analysis data"""
    company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    # Parse date range
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Average sentiment
    avg_sentiment = db.session.query(
        func.avg(Conversation.sentiment_score)
    ).filter(
        Conversation.company_id == company.id,
        Conversation.started_at >= start_date,
        Conversation.sentiment_score != None
    ).scalar() or 0
    
    # Sentiment distribution
    positive = Conversation.query.filter(
        Conversation.company_id == company.id,
        Conversation.started_at >= start_date,
        Conversation.sentiment_score != None,
        Conversation.sentiment_score > 0.3
    ).count()
    
    neutral = Conversation.query.filter(
        Conversation.company_id == company.id,
        Conversation.started_at >= start_date,
        Conversation.sentiment_score != None,
        Conversation.sentiment_score >= -0.3,
        Conversation.sentiment_score <= 0.3
    ).count()
    
    negative = Conversation.query.filter(
        Conversation.company_id == company.id,
        Conversation.started_at >= start_date,
        Conversation.sentiment_score != None,
        Conversation.sentiment_score < -0.3
    ).count()
    
    return jsonify({
        'average_sentiment': round(avg_sentiment, 2),
        'distribution': {
            'positive': positive,
            'neutral': neutral,
            'negative': negative
        },
        'period_days': days
    })

@analytics_bp.route('/customers', methods=['GET'])
@jwt_required()
def get_customer_stats():
    """Get registered customer stats (Contacts with Data)"""
    company = get_user_company()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
        
    # Count customers with valid data (Name, Email OR Phone)
    # Assuming 'Customer' table already implies some data, but verifying.
    # User said: "solo son los contactos donde tenemos datos, es decir correo, nombre"
    
    count = Customer.query.filter(
        Customer.company_id == company.id,
        (Customer.email != None) | (Customer.phone != None) | (Customer.first_name != None)
    ).count()
    
    return jsonify({
        'count': count,
        'label': 'Clientes Registrados'
    })
