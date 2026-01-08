import psycopg2

try:
    conn = psycopg2.connect(database="cardpulse")
    cur = conn.cursor()
    cur.execute("SELECT product_id, player_name, set_name, card_number, epid FROM cards;")
    rows = cur.fetchall()
    
    print(f"{'ID':<5} | {'Player':<20} | {'Set':<25} | {'#':<5} | {'EPID'}")
    print("-" * 80)
    for row in rows:
        epid = row[4] if row[4] else "MISSING"
        print(f"{row[0]:<5} | {row[1]:<20} | {row[2]:<25} | {row[3]:<5} | {epid}")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
