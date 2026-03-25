import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Path to the .env file in the backend directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

def test_connection():
    print(f"\n--- EnpiAI Database Connection Diagnostic ---")
    print(f"Location: {os.path.abspath(__file__)}")
    print(f"Loading .env from: {env_path}")
    
    # Check variables
    mysql_host = os.getenv('MYSQL_HOST')
    mysql_user = os.getenv('MYSQL_USER')
    mysql_db = os.getenv('MYSQL_DATABASE', 'enpi_ai')
    mysql_port = os.getenv('MYSQL_PORT', '3306')
    db_url = os.getenv('DATABASE_URL')
    
    print(f"\nEnvironment variables captured:")
    print(f"  MYSQL_HOST: {mysql_host}")
    print(f"  MYSQL_USER: {mysql_user}")
    print(f"  MYSQL_DATABASE: {mysql_db}")
    print(f"  MYSQL_PORT: {mysql_port}")
    print(f"  DATABASE_URL set: {'Yes' if db_url else 'No'}")
    
    if db_url:
        uri = db_url
    elif mysql_host and mysql_user:
        password = os.getenv('MYSQL_PASSWORD', '')
        # Mask password for logs
        masked_pwd = password[:2] + '*' * (len(password)-2) if password else 'EMPTY'
        print(f"  MYSQL_PASSWORD: {masked_pwd}")
        uri = f"mysql+pymysql://{mysql_user}:{password}@{mysql_host}:{mysql_port}/{mysql_db}"
    else:
        print("\n❌ ERROR: Missing MySQL environment variables in .env.")
        print("Ensure MYSQL_HOST, MYSQL_USER, and MYSQL_PASSWORD are set.")
        return

    print(f"\nAttempting to connect to: {uri.split('@')[-1]} (password masked)")
    
    try:
        # Use a short timeout for the test
        engine = create_engine(uri, connect_args={"connect_timeout": 10})
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            val = result.scalar()
            if val == 1:
                print("\n✅ SUCCESS: Connection established and query executed.")
            else:
                print(f"\n⚠️ WARNING: Connected but query returned unexpected result: {val}")
                
            # Check table existence (test if migrations ran)
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"  Tables found in database: {len(tables)}")
            if len(tables) > 0:
                print(f"  Sample tables: {', '.join(tables[:5])}")
            else:
                print("  ⚠️ WARNING: No tables found. Database might be empty. Did you run migrations?")

    except Exception as e:
        print(f"\n❌ CONNECTION FAILED:")
        print(f"  Error Type: {type(e).__name__}")
        print(f"  Error Details: {str(e)}")
        
        if "Access denied" in str(e):
            print("\n💡 TIP: Check your MYSQL_USER and MYSQL_PASSWORD. Ensure the user has permissions for the database.")
        elif "Can't connect to MySQL server" in str(e):
            print("\n💡 TIP: Check if the MySQL service is running on the host and if the port is correct.")
            print("  - If MySQL is on the same VPS, use 'localhost' or '127.0.0.1'.")
            print("  - Check VPS firewall settings (though local connections are usually open).")
        elif "Unknown database" in str(e):
            print("\n💡 TIP: The database name in MYSQL_DATABASE does not exist. Create it manually first: `CREATE DATABASE enpiai;`")

if __name__ == "__main__":
    test_connection()
