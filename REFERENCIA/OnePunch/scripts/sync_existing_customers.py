import sys
import os
import time

sys.path.append(os.getcwd())

from app import create_app
from extensions import db
from models.company import Company
from models.customer import Customer
from models.appointment import Appointment
from models.transaction import Transaction
from models.conversation import Conversation
from services.hubspot_service import HubSpotService

app = create_app()

def determine_status(customer):
    """
    Determine correct Lifecycle Stage and Lead Status based on history.
    """
    # 1. Transactions - Highest Priority (Customer)
    tx_count = Transaction.query.filter_by(customer_id=customer.id, status='completed').count()
    if tx_count > 0:
        return 'customer', 'CONNECTED'
        
    # 2. Appointments - High Priority (Opportunity)
    app_count = Appointment.query.filter_by(customer_id=customer.id).count()
    if app_count > 0:
        return 'opportunity', 'OPEN_DEAL'
        
    # 3. Conversations - Medium Priority (In Progress)
    # Check by email or phone
    from sqlalchemy import or_
    conv_count = Conversation.query.filter(
        or_(
            Conversation.contact_email == customer.email,
            Conversation.contact_phone == customer.phone
        )
    ).count()
    if conv_count > 0:
        return 'lead', 'IN_PROGRESS'
        
    # 4. Default - New Lead
    return 'lead', 'NEW'

with app.app_context():
    # Loop primarily for Company 1 as requester context implies
    company = Company.query.get(1)
    if not company:
        print("Company 1 not found")
        sys.exit(1)
        
    print(f"--- Starting Backfill for {company.name} ---")
    service = HubSpotService(company=company)
    
    customers = Customer.query.filter_by(company_id=company.id).all()
    print(f"Found {len(customers)} customers.")
    
    success_count = 0
    error_count = 0
    
    for customer in customers:
        if not customer.email:
            print(f"Skipping Customer {customer.id} (No Email)")
            continue
            
        stage, status = determine_status(customer)
        print(f"Syncing {customer.email} -> Stage: {stage}, Status: {status}")
        
        try:
            # We explicitly update stage and status
            # HubSpotService already separates lifecycle update logic partially but create_or_update handles properties
            # We need to ensure lifecycle is updated if it's 'customer' or 'opportunity'
            
            # 1. Sync Contact Properties (Lead Status, Buying Role, etc.)
            service.create_or_update_contact(
                email=customer.email,
                firstname=customer.first_name,
                lastname=customer.last_name,
                phone=customer.phone,
                buying_role=customer.buying_role,
                lead_status=status
            )
            
            # 2. Force lifecycle update if needed
            # create_or_update sets default 'lead' but doesn't upgrade usually
            if stage == 'customer':
                print(f"   -> Updating Lifecycle to CUSTOMER")
                result = service.update_lifecycle_to_customer(customer.email)
                print(f"   -> Result: {result}")
            elif stage == 'opportunity':
                print(f"   -> Updating Lifecycle to OPPORTUNITY")
                result = service.mark_as_scheduled(customer.email)
                print(f"   -> Result: {result}")
            
            success_count += 1
            # Rate limit slightly to avoid spamming if list is huge
            time.sleep(0.5) 
            
        except Exception as e:
            print(f"   ERROR: {e}")
            error_count += 1
            
    print(f"\n--- Backfill Complete ---")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")
