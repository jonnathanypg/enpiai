import os
import sys
from app import create_app
from extensions import db
from models.user import User
from models.distributor import Distributor

def fix_data():
    app = create_app()
    with app.app_context():
        print("--- EnpiAI Production Data Repair ---")
        
        # 1. Ensure at least one distributor exists
        distributor = Distributor.query.first()
        if not distributor:
            print("Creating default distributor...")
            distributor = Distributor(
                name="Principal",
                email="admin@enpi.click",
                is_active=True
            )
            db.session.add(distributor)
            db.session.commit()
            print(f"✅ Created Distributor: {distributor.name} (ID: {distributor.id})")
        else:
            print(f"✅ Found Distributor: {distributor.name} (ID: {distributor.id})")

        # 2. Link all users to this distributor if they don't have one
        users_fixed = 0
        users = User.query.all()
        for user in users:
            if not user.distributor_id:
                user.distributor_id = distributor.id
                users_fixed += 1
                print(f"  Linking user {user.email} to distributor {distributor.id}")
        
        if users_fixed > 0:
            db.session.commit()
            print(f"✅ Fixed {users_fixed} users.")
        else:
            print("✅ All users already have a distributor_id.")

        print("\n--- Repair Complete ---")

if __name__ == "__main__":
    fix_data()
