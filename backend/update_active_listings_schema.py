import psycopg2

def update_schema():
    try:
        conn = psycopg2.connect(database="cardpulse")
        cur = conn.cursor()
        
        print("Updating active_listings schema columns...")
        
        # Add columns if they don't exist
        columns = {
            "grader": "VARCHAR(50)",
            "grade": "VARCHAR(20)",
            "product_id": "INTEGER", 
            "is_ignored": "BOOLEAN DEFAULT FALSE"
        }
        
        for col, dtype in columns.items():
            # Check existence
            cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='active_listings' AND column_name='{col}'")
            if not cur.fetchone():
                print(f"Adding column: {col}")
                cur.execute(f"ALTER TABLE active_listings ADD COLUMN {col} {dtype}")
                
        # Add FK constraint for product_id
        # Check constraint existence
        cur.execute("SELECT conname FROM pg_constraint WHERE conname = 'fk_active_product'")
        if not cur.fetchone():
            print("Adding FK constraint...")
            cur.execute("ALTER TABLE active_listings ADD CONSTRAINT fk_active_product FOREIGN KEY (product_id) REFERENCES cards(product_id)")

        conn.commit()
        cur.close()
        conn.close()
        print("Schema update complete.")
        
    except Exception as e:
        print(f"Error updating schema: {e}")

if __name__ == "__main__":
    update_schema()
