from app import create_app
from extensions import db
from sqlalchemy import inspect, text

app = create_app()

with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Tables found: {tables}")

    # expected columns per table
    expected = {
        'distributors': ['language', 'api_key', 'api_keys', 'google_credentials', 'subscription_tier'],
        'users': ['google_credentials'],
        'customers': ['email', 'phone', 'ident_number'], # encrypted fields check
        'leads': ['email', 'phone'],
        'wellness_evaluations': ['health_conditions', 'allergies', 'medications']
    }

    missing_log = []

    for table, columns in expected.items():
        if table not in tables:
            missing_log.append(f"MISSING TABLE: {table}")
            continue
            
        existing_cols = [c['name'] for c in inspector.get_columns(table)]
        for col in columns:
            if col not in existing_cols:
                missing_log.append(f"MISSING COLUMN: {table}.{col}")
            else:
                print(f"✅ {table}.{col} exists")

    if missing_log:
        print("\n❌ MIGRATION REQUIRED:")
        for msg in missing_log:
            print(msg)
            
        # Attempt minimal migration script generation suggestion
        print("\nSUGGESTED SQL:")
        for msg in missing_log:
            if "MISSING COLUMN" in msg:
                parts = msg.split(": ")[1].split(".")
                tbl, col = parts[0], parts[1]
                if col == 'language':
                    print(f"ALTER TABLE {tbl} ADD COLUMN {col} VARCHAR(5) DEFAULT 'en';")
                elif col == 'api_key':
                    print(f"ALTER TABLE {tbl} ADD COLUMN {col} VARCHAR(255);")
                    print(f"CREATE INDEX idx_{tbl}_{col} ON {tbl}({col});")
                elif col == 'subscription_tier':
                    print(f"ALTER TABLE {tbl} ADD COLUMN {col} VARCHAR(20) DEFAULT 'free';")
                elif col in ['api_keys', 'google_credentials']:
                    print(f"ALTER TABLE {tbl} ADD COLUMN {col} JSON;")
                else:
                    print(f"ALTER TABLE {tbl} ADD COLUMN {col} TEXT;") # Fallback for encrypted fields
    else:
        print("\n✅ DATABASE SCHEMA IS SYNCED!")
