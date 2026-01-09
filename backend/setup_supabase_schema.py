from database import get_db_connection

def create_schema():
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("Creating tables on Supabase/Remote DB...")
    
    # 1. Cards Table (With Variant Support)
    # Note: We need the UNIQUE constraint to include grade/grader for variants
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            product_id SERIAL PRIMARY KEY,
            epid VARCHAR(255),
            player_name VARCHAR(255),
            year INTEGER,
            set_name VARCHAR(255),
            subset_insert VARCHAR(255),
            card_number VARCHAR(50),
            grader VARCHAR(50) DEFAULT 'Raw',
            grade VARCHAR(20) DEFAULT 'Raw',
            UNIQUE(epid, player_name, year, set_name, subset_insert, card_number, grader, grade)
        );
    """)
    print("- cards table created.")

    # 2. Sales Table (Historic Sold Data)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id SERIAL PRIMARY KEY,
            product_id INTEGER REFERENCES cards(product_id),
            date DATE,
            grade VARCHAR(50),
            price NUMERIC,
            source VARCHAR(50)
        );
    """)
    print("- sales table created.")

    # 3. Forecasts Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS forecasts (
            id SERIAL PRIMARY KEY,
            product_id INTEGER REFERENCES cards(product_id),
            forecast_date DATE,
            predicted_price NUMERIC,
            confidence_interval_lower NUMERIC,
            confidence_interval_upper NUMERIC,
            model_version VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("- forecasts table created.")

    # 4. Active Listings Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS active_listings (
            id SERIAL PRIMARY KEY,
            item_id VARCHAR(255) UNIQUE NOT NULL,
            legacy_item_id VARCHAR(50),
            title TEXT,
            price NUMERIC(10, 2),
            currency VARCHAR(10),
            buying_options TEXT,
            listing_url TEXT,
            image_url TEXT,
            item_location JSONB,
            priority_listing BOOLEAN,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            origin_date TIMESTAMP,
            search_query TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            grader VARCHAR(50),
            grade VARCHAR(20),
            product_id INTEGER REFERENCES cards(product_id),
            is_ignored BOOLEAN DEFAULT FALSE
        );
    """)
    # Index for speed
    cur.execute("CREATE INDEX IF NOT EXISTS idx_active_item ON active_listings(item_id);")
    print("- active_listings table created.")

    conn.commit()
    cur.close()
    conn.close()
    print("Schema migration successful.")

if __name__ == "__main__":
    create_schema()
