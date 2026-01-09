
import os
from database import get_db_connection

def apply_tiered_refresh_schema():
    print("Applying tiered refresh schema update...")
    conn = get_db_connection()
    cur = conn.cursor()
    
    sql_file = os.path.join(os.path.dirname(__file__), 'db', 'update_schema_tiered_refresh.sql')
    
    with open(sql_file, 'r') as f:
        sql = f.read()
        
    try:
        cur.execute(sql)
        conn.commit()
        print("Tiered refresh schema applied successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error applying schema: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    apply_tiered_refresh_schema()
