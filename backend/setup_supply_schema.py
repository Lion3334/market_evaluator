from database import get_db_connection

def setup_supply_schema():
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("Setting up Supply Metrics Schema on Supabase...")
    
    # Create daily_supply_metrics table
    # Unique constraint on (product_id, date) to allow upserts
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_supply_metrics (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL,
            product_id INTEGER, -- Intentionally not FK to cards yet to allow decoupled updates, but logically linked
            
            -- New Listing Counts (The "Shock")
            new_count_fixed_price_only INTEGER DEFAULT 0,
            new_count_best_offer INTEGER DEFAULT 0,
            new_count_auction INTEGER DEFAULT 0,
            
            -- Total Active Depth
            total_active_fixed_price_only INTEGER DEFAULT 0,
            total_active_best_offer INTEGER DEFAULT 0,
            total_active_auction INTEGER DEFAULT 0,
            
            -- Price Signals
            median_new_price NUMERIC(10, 2), -- Calculated from FIXED_PRICE types only
            
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(product_id, date)
        );
    """)
    print("- daily_supply_metrics table created/verified.")

    conn.commit()
    cur.close()
    conn.close()
    print("Supply schema setup complete.")

if __name__ == "__main__":
    setup_supply_schema()
