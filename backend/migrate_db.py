from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Starting migration...")
    try:
        # 1. Add api_key column
        print("Adding api_key column...")
        try:
            db.session.execute(text("ALTER TABLE distributors ADD COLUMN api_key VARCHAR(255);"))
            db.session.execute(text("CREATE INDEX idx_distributors_api_key ON distributors(api_key);"))
            print("✅ api_key added")
        except Exception as e:
            print(f"⚠️ api_key skipped (maybe exists): {e}")

        # 2. Add google_credentials column
        print("Adding google_credentials column...")
        try:
            db.session.execute(text("ALTER TABLE distributors ADD COLUMN google_credentials JSON;"))
            print("✅ google_credentials added")
        except Exception as e:
            print(f"⚠️ google_credentials skipped (maybe exists): {e}")

        db.session.commit()
        print("\nMigration complete!")

    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Migration failed: {e}")
