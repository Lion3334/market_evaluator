from database import get_db_connection

def migrate_schema():
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("Migrating Schema: Adding missing columns to 'cards' table...")
    
    columns_to_add = [
        ("manufacturer", "VARCHAR(50)"),
        ("sport", "VARCHAR(50)"),
        ("is_rookie_card", "BOOLEAN DEFAULT FALSE"),
        ("is_serial_numbered", "BOOLEAN DEFAULT FALSE"),
        ("print_run", "INTEGER"),
        ("url", "TEXT"),
        ("parallel_type", "VARCHAR(100) DEFAULT 'Base'"),
        ("variation_type", "VARCHAR(100)")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            # Check if column exists
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='cards' AND column_name=%s
            """, (col_name,))
            if not cur.fetchone():
                print(f"Adding column: {col_name}")
                cur.execute(f"ALTER TABLE cards ADD COLUMN {col_name} {col_type};")
            else:
                print(f"Column {col_name} already exists.")
        except Exception as e:
            print(f"Error checking/adding {col_name}: {e}")
            conn.rollback()

    conn.commit()
    cur.close()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate_schema()
