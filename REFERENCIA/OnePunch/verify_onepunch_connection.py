
import sys
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from sqlalchemy import text

print("\n🚀 Testing OnePunch Real Connection...")
app = create_app()

with app.app_context():
    try:
        print(f"   Target: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[-1]}")
        print("   Connecting...")
        # Force connection
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT MAX(id) FROM companies"))
            print(f"   ✅ SUCCESS! Connected. Result: {result.fetchone()}")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
