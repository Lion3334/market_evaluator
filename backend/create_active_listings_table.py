import psycopg2

def create_table():
    try:
        conn = psycopg2.connect(database="cardpulse")
        cur = conn.cursor()
        
        print("Creating active_listings table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS active_listings (
                id SERIAL PRIMARY KEY,
                item_id VARCHAR(255) UNIQUE NOT NULL,
                legacy_item_id VARCHAR(50),
                title TEXT,
                price NUMERIC(10, 2),
                currency VARCHAR(10),
                buying_options TEXT,  -- Storing as comma-separated string or could use TEXT[]
                listing_url TEXT,
                image_url TEXT,
                item_location JSONB,
                priority_listing BOOLEAN,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                origin_date TIMESTAMP,
                search_query TEXT,    -- To track what search found this
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Add index on item_id for faster lookups/upserts
        cur.execute("CREATE INDEX IF NOT EXISTS idx_active_item ON active_listings(item_id);")
        
        conn.commit()
        cur.close()
        conn.close()
        print("Table 'active_listings' created successfully.")
        
    except Exception as e:
        print(f"Error creating table: {e}")

if __name__ == "__main__":
    create_table()
