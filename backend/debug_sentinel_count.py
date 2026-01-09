
from database import get_db_connection

def check_count():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT count(*) FROM sentinel_sales")
        print(f"Sentinel Sales Count: {cur.fetchone()[0]}")
    except Exception as e:
        print(f"Error: {e}")
    conn.close()

if __name__ == "__main__":
    check_count()
