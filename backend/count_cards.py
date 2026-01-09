from database import get_db_connection

def count_cards():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM cards;")
    count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM cards WHERE set_name='Panini Illusions' AND year=2023;")
    illusions_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM cards WHERE set_name='Panini Illusions' AND year=2023 AND epid IS NOT NULL;")
    epid_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM active_listings;")
    active_count = cur.fetchone()[0]
    
    print(f"Total Cards in DB: {count}")
    print(f"Total '2023 Panini Illusions': {illusions_count}")
    print(f"Illusions with EPID: {epid_count}")
    print(f"Total Active Listings: {active_count}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    count_cards()
