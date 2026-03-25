import os
import sys
import bcrypt
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Path to the .env file in the backend directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

def test_login_logic():
    print(f"\n--- EnpiAI Login & User Diagnostic ---")
    
    # 1. Get Connection URI
    mysql_host = os.getenv('MYSQL_HOST')
    mysql_user = os.getenv('MYSQL_USER')
    mysql_db = os.getenv('MYSQL_DATABASE', 'enpi_ai')
    mysql_port = os.getenv('MYSQL_PORT', '3306')
    mysql_pass = os.getenv('MYSQL_PASSWORD', '')
    db_url = os.getenv('DATABASE_URL')
    
    uri = db_url if db_url else f"mysql+pymysql://{mysql_user}:{mysql_pass}@{mysql_host}:{mysql_port}/{mysql_db}"
    
    try:
        engine = create_engine(uri)
        with engine.connect() as conn:
            # 2. Check users in DB
            print("\n1. Checking Users table...")
            result = conn.execute(text("SELECT id, email, name, is_active, password_hash FROM users LIMIT 5"))
            users = result.fetchall()
            
            if not users:
                print("❌ ERROR: No users found in the 'users' table. Did you run seed_users.py or register?")
                return

            print(f"✅ Found {len(users)} users. Testing first user...")
            for user in users:
                u_id, u_email, u_name, u_active, u_hash = user
                print(f"\nTest User: {u_name} ({u_email})")
                print(f"Status: {'Active' if u_active else 'Inactive'}")
                
                # 3. Test Bcrypt functionality
                print("2. Testing Bcrypt compatibility...")
                # Note: This is a simulation. We'd usually check against a known password.
                # Since we don't know the password, we just check if the hash is valid format.
                try:
                    is_valid_hash = u_hash.startswith('$2b$') or u_hash.startswith('$2a$')
                    if is_valid_hash:
                        print(f"✅ Password hash format looks valid (bcrypt).")
                    else:
                        print(f"❌ WARNING: Password hash format unknown: {u_hash[:10]}...")
                except Exception as e:
                    print(f"❌ ERROR checking hash: {e}")

            # 4. Check Distributor
            print("\n3. Checking Distributors...")
            result = conn.execute(text("SELECT count(*) FROM distributors"))
            dist_count = result.scalar()
            print(f"✅ Found {dist_count} distributors.")

            # 5. Check JWT Secret
            print("\n4. Checking Security Keys...")
            jwt_secret = os.getenv('JWT_SECRET_KEY')
            if not jwt_secret or jwt_secret == 'jwt-secret-key-change-in-production':
                print("⚠️ WARNING: JWT_SECRET_KEY is default or missing. This might cause token issues.")
            else:
                print("✅ JWT_SECRET_KEY is configured.")

            # 6. Check CORS
            cors = os.getenv('CORS_ORIGINS', '*')
            print(f"CORS_ORIGINS: {cors}")
            if cors != '*' and '109.205.180.23' not in cors:
                 print("⚠️ WARNING: Current VPS IP not in CORS_ORIGINS. Browser might block requests.")

    except Exception as e:
        print(f"\n❌ DIAGNOSTIC FAILED: {e}")

if __name__ == "__main__":
    test_login_logic()
