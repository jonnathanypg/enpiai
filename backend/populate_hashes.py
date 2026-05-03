import os
from app import create_app
from extensions import db
from models.lead import Lead
from models.customer import Customer

app = create_app()
with app.app_context():
    try:
        # Populate Leads
        leads = Lead.query.all()
        print(f"Populating hashes for {len(leads)} leads...")
        for lead in leads:
            if lead.email and not lead.email_hash:
                lead.email_hash = Lead.generate_hash(lead.email)
            if lead.phone and not lead.phone_hash:
                lead.phone_hash = Lead.generate_hash(lead.phone)
        
        # Populate Customers
        customers = Customer.query.all()
        print(f"Populating hashes for {len(customers)} customers...")
        for cust in customers:
            if cust.email and not cust.email_hash:
                cust.email_hash = Lead.generate_hash(cust.email)
            if cust.phone and not cust.phone_hash:
                cust.phone_hash = Lead.generate_hash(cust.phone)
        
        db.session.commit()
        print("Hash population successful.")
    except Exception as e:
        db.session.rollback()
        print(f"Error during population: {e}")
