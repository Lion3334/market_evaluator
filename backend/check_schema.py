import psycopg2

try:
    conn = psycopg2.connect(database="cardpulse")
    cur = conn.cursor()
    # Get columns for 'cards' table
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'cards'
        ORDER BY ordinal_position;
    """)
    rows = cur.fetchall()
    
    print("Table: CARDS")
    print(f"{'Column':<20} | {'Type':<15} | {'Nullable'}")
    print("-" * 50)
    for row in rows:
        print(f"{row[0]:<20} | {row[1]:<15} | {row[2]}")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
