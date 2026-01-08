import psycopg2

try:
    conn = psycopg2.connect(database="cardpulse")
    cur = conn.cursor()
    
    # Check if columns exist first to avoid error
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='forecasts' AND column_name='grade';
    """)
    if not cur.fetchone():
        print("Adding 'grade' column...")
        cur.execute("ALTER TABLE forecasts ADD COLUMN grade VARCHAR(20);")
        
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='forecasts' AND column_name='grader';
    """)
    if not cur.fetchone():
        print("Adding 'grader' column...")
        cur.execute("ALTER TABLE forecasts ADD COLUMN grader VARCHAR(50);")

    conn.commit()
    conn.close()
    print("Schema update complete.")
except Exception as e:
    print(f"Error: {e}")
