from database import get_db_connection

def setup_price_history():
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("Setting up Price History Tracking on Supabase...")
    
    # 1. Create History Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS listing_price_changes (
            id SERIAL PRIMARY KEY,
            item_id VARCHAR(255) REFERENCES active_listings(item_id),
            old_price NUMERIC(10, 2),
            new_price NUMERIC(10, 2),
            change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("- listing_price_changes table created/verified.")

    # 2. Create Trigger Function
    cur.execute("""
        CREATE OR REPLACE FUNCTION log_price_change_func() RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.price <> OLD.price THEN
                INSERT INTO listing_price_changes (item_id, old_price, new_price)
                VALUES (OLD.item_id, OLD.price, NEW.price);
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    print("- Trigger function 'log_price_change_func' created.")

    # 3. Attach Trigger to Active Listings Table
    cur.execute("DROP TRIGGER IF EXISTS trigger_log_price_change ON active_listings;")
    cur.execute("""
        CREATE TRIGGER trigger_log_price_change
        BEFORE UPDATE ON active_listings
        FOR EACH ROW
        EXECUTE FUNCTION log_price_change_func();
    """)
    print("- Trigger 'trigger_log_price_change' attached to active_listings.")

    conn.commit()
    cur.close()
    conn.close()
    print("Price history setup complete.")

if __name__ == "__main__":
    setup_price_history()
