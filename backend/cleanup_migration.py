import os
from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        # Check if columns exist
        result = db.session.execute(text("SHOW COLUMNS FROM leads"))
        columns = [row[0] for row in result]
        print(f"Current columns in 'leads': {columns}")
        
        if 'email_hash' in columns:
            print("Dropping email_hash...")
            db.session.execute(text("ALTER TABLE leads DROP COLUMN email_hash"))
        if 'phone_hash' in columns:
            print("Dropping phone_hash...")
            db.session.execute(text("ALTER TABLE leads DROP COLUMN phone_hash"))
            
        # Also check for partial indexes
        result = db.session.execute(text("SHOW INDEX FROM leads"))
        indexes = [row[2] for row in result]
        print(f"Current indexes in 'leads': {indexes}")
        
        if 'ix_leads_email_hash' in indexes:
             db.session.execute(text("DROP INDEX ix_leads_email_hash ON leads"))
        if 'ix_leads_phone_hash' in indexes:
             db.session.execute(text("DROP INDEX ix_leads_phone_hash ON leads"))

        db.session.commit()
        print("Cleanup successful.")
    except Exception as e:
        db.session.rollback()
        print(f"Error during cleanup: {e}")
