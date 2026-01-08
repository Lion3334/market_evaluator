import psycopg2

try:
    conn = psycopg2.connect(database="cardpulse")
    cur = conn.cursor()
    
    # Select all Drake Maye cards
    cur.execute("""
        SELECT product_id, player_name, set_name, subset_insert, card_number, grader, grade, epid 
        FROM cards 
        WHERE player_name = 'Drake Maye'
        ORDER BY product_id;
    """)
    rows = cur.fetchall()
    
    print(f"{'ID':<5} | {'Variant':<20} | {'Grader':<8} | {'Grade':<5} | {'EPID'}")
    print("-" * 80)
    for row in rows:
        pid, player, set_n, subset, num, grader, grade, epid = row
        variant = f"{subset} #{num}"
        print(f"{pid:<5} | {variant:<20} | {grader:<8} | {grade:<5} | {epid}")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
