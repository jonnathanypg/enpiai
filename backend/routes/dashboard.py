"""
Dashboard Routes - Analytics and Metrics
"""
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from sqlalchemy import func, and_

from extensions import db
from models.lead import Lead, LeadStatus
from models.customer import Customer
from models.conversation import Conversation, ConversationStatus, Message
from models.distributor import Distributor
from routes.auth import jwt_required, get_current_distributor

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/metrics', methods=['GET'])
@jwt_required()
def get_metrics():
    """
    Get dashboard key metrics for the current distributor.
    - Total Leads
    - Qualified Leads
    - Total Customers
    - Messages Today
    - Active Conversations
    - Conversion Rate
    """
    current_distributor = get_current_distributor()
    if not current_distributor:
        return jsonify({'error': 'Distributor context required'}), 403

    distributor_id = current_distributor.id
    
    # 1. Leads Stats
    total_leads = Lead.query.filter_by(distributor_id=distributor_id).count()
    qualified_leads = Lead.query.filter_by(
        distributor_id=distributor_id, 
        status=LeadStatus.QUALIFIED
    ).count()

    # 2. Customers
    total_customers = Customer.query.filter_by(distributor_id=distributor_id).count()

    # 3. Messages Today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    messages_today = Message.query.join(Conversation).filter(
        Conversation.distributor_id == distributor_id,
        Message.created_at >= today_start
    ).count()

    # 4. Active Conversations (Active status)
    active_conversations = Conversation.query.filter_by(
        distributor_id=distributor_id,
        status=ConversationStatus.ACTIVE
    ).count()

    # 5. Conversion Rate (Customers / (Leads + Customers) * 100) or just Customers/TotalLeads
    # Standard: Leads who became customers.
    # If Lead is deleted when converted, then Total Leads = Current Leads.
    # Let's assume Total Unique Contacts = Leads + Customers.
    # Conversion Rate = Customers / (Leads + Customers) if exclusive.
    # But usually models are separate.
    # Simplest: Customers / (Leads + Customers) if we assume no overlap, or Customers / Total Opportunities.
    # Let's use (Customers / (Total Leads + Total Customers)) for now if they are disjoint.
    # Actually Lead might stay as 'CONVERTED'.
    converted_leads = Lead.query.filter_by(
        distributor_id=distributor_id, 
        status=LeadStatus.CONVERTED
    ).count()
    
    # The actual conversion rate is usually Converted / Total.
    rate_denominator = total_leads 
    conversion_rate = 0.0
    if rate_denominator > 0:
        conversion_rate = (converted_leads / rate_denominator) * 100
        
    return jsonify({
        'total_leads': total_leads,
        'qualified_leads': qualified_leads,
        'total_customers': total_customers,
        'messages_today': messages_today,
        'active_conversations': active_conversations,
        'conversion_rate': round(conversion_rate, 1)
    }), 200
