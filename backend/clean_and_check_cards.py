from database import get_db_connection

def clean_cards():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check count before
    cur.execute("SELECT COUNT(*) FROM cards;")
    before = cur.fetchone()[0]
    
    # Check for empty player names
    cur.execute("SELECT COUNT(*) FROM cards WHERE player_name = '' OR player_name IS NULL;")
    bad_count = cur.fetchone()[0]
    
    print(f"Total Cards: {before}")
    print(f"Bad Cards (Empty Name): {bad_count}")
    
    if bad_count > 0:
        print("Cleaning bad rows...")
        cur.execute("DELETE FROM cards WHERE player_name = '' OR player_name IS NULL;")
        conn.commit()
        
        cur.execute("SELECT COUNT(*) FROM cards;")
        after = cur.fetchone()[0]
        print(f"Cleanup Complete. Rows remaining: {after}")
    else:
        print("No bad rows found.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    clean_cards()
