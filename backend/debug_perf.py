
from database import get_db_connection
from datetime import date

def check_perf():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM daily_model_performance WHERE date = %s", (date.today(),))
        row = cur.fetchone()
        if row:
            print(f"Performance Record Found: {row}")
        else:
            print("No performance record found for today.")
            
        cur.execute("SELECT count(*) FROM price_history WHERE actual_sold_price IS NOT NULL")
        count = cur.fetchone()[0]
        print(f"Validated Price History Rows: {count}")
        
    except Exception as e:
        print(f"Error: {e}")
    conn.close()

if __name__ == "__main__":
    check_perf()
