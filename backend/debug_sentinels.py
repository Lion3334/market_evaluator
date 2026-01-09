
from database import get_db_connection

def debug_sentinels():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT product_id, player_name, grader, grade, url FROM cards WHERE is_sentinel = TRUE LIMIT 5")
        rows = cur.fetchall()
        print(f"Found {len(rows)} sentinels.")
        for r in rows:
            print(r)
    except Exception as e:
        print(f"Error: {e}")
    conn.close()

if __name__ == "__main__":
    debug_sentinels()
