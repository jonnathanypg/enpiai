"""
Migration script to ensure all Nutrition Club columns and tables exist.
"""
from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app(start_services=False)

with app.app_context():
    conn = db.engine.connect()
    
    # 1. Update distributors table
    print("Checking distributors table...")
    dist_cols = [
        ("club_name", "VARCHAR(255) NULL"),
        ("club_slogan", "VARCHAR(255) NULL"),
        ("club_address", "VARCHAR(500) NULL"),
        ("club_city", "VARCHAR(100) NULL"),
        ("club_schedule", "VARCHAR(255) NULL"),
        ("club_phone", "VARCHAR(50) NULL"),
        ("club_latitude", "FLOAT NULL"),
        ("club_longitude", "FLOAT NULL"),
        ("club_banner_url", "VARCHAR(500) NULL"),
        ("club_logo_url", "VARCHAR(500) NULL"),
        ("club_is_active", "BOOLEAN DEFAULT TRUE"),
        ("club_amenities", "JSON NULL"),
        ("club_announcement", "TEXT NULL"),
    ]
    
    for col_name, col_type in dist_cols:
        try:
            conn.execute(text(f"ALTER TABLE distributors ADD COLUMN {col_name} {col_type};"))
            conn.commit()
            print(f"✅ Added distributors.{col_name}")
        except Exception as e:
            if "Duplicate column" in str(e) or "already exists" in str(e) or "duplicate column name" in str(e).lower():
                print(f"ℹ️ distributors.{col_name} already exists")
            else:
                print(f"⚠️ distributors.{col_name} notice: {e}")

    # 2. Update products table
    print("\nChecking products table...")
    prod_cols = [
        ("is_club_menu", "BOOLEAN DEFAULT TRUE"),
        ("protein_grams", "FLOAT NULL"),
        ("calories", "INT NULL"),
        ("preparation_time_min", "INT DEFAULT 5"),
        ("customization_options", "JSON NULL"),
        ("display_order", "INT DEFAULT 0"),
    ]
    for col_name, col_type in prod_cols:
        try:
            conn.execute(text(f"ALTER TABLE products ADD COLUMN {col_name} {col_type};"))
            conn.commit()
            print(f"✅ Added products.{col_name}")
        except Exception as e:
            if "Duplicate column" in str(e) or "already exists" in str(e) or "duplicate column name" in str(e).lower():
                print(f"ℹ️ products.{col_name} already exists")
            else:
                print(f"⚠️ products.{col_name} notice: {e}")

    # 3. Create club_orders table
    print("\nChecking club_orders table...")
    create_orders_sql = """
    CREATE TABLE IF NOT EXISTS club_orders (
        id INT AUTO_INCREMENT PRIMARY KEY,
        distributor_id INT NOT NULL,
        order_number VARCHAR(50) NULL,
        customer_name VARCHAR(255) NOT NULL,
        customer_phone VARCHAR(50) NULL,
        customer_email VARCHAR(255) NULL,
        delivery_type VARCHAR(50) DEFAULT 'dine_in',
        items JSON NOT NULL,
        subtotal FLOAT DEFAULT 0.0,
        total FLOAT DEFAULT 0.0,
        currency VARCHAR(10) DEFAULT 'USD',
        notes TEXT NULL,
        status VARCHAR(50) DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_club_orders_distributor (distributor_id),
        CONSTRAINT fk_club_orders_distributor FOREIGN KEY (distributor_id) REFERENCES distributors(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    try:
        conn.execute(text(create_orders_sql))
        conn.commit()
        print("✅ club_orders table is ready!")
    except Exception as e:
        print(f"⚠️ club_orders table error/notice: {e}")

    conn.close()
    print("\n🎉 Nutrition Club database migration complete!")
