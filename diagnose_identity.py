
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app import create_app
from extensions import db
from models.distributor import Distributor
from services.identity_resolver import IdentityResolver

app = create_app()

def diagnose_identity(phone, distributor_id):
    with app.app_context():
        dist = Distributor.query.get(distributor_id)
        if not dist:
            print(f"Distributor {distributor_id} not found.")
            return
        
        print(f"Diagnosing for Distributor: {dist.name} (ID: {dist.id})")
        print(f"Stored Phone: {dist.phone}")
        print(f"Stored WhatsApp Phone: {dist.whatsapp_phone}")
        print(f"Incoming Phone: {phone}")
        
        identity = IdentityResolver.resolve_from_phone(phone, distributor_id)
        print(f"Resolution Result: {identity}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python diagnose_identity.py <phone> <distributor_id>")
    else:
        diagnose_identity(sys.argv[1], int(sys.argv[2]))
