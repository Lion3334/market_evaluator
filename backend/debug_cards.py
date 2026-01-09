
from database import get_db_connection

def check_urls():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT product_id, player_name, url FROM cards WHERE is_sentinel = TRUE LIMIT 5")
    rows = cur.fetchall()
    for r in rows:
        print(r)
    conn.close()

if __name__ == "__main__":
    check_urls()
