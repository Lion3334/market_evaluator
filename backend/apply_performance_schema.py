
import os
from database import get_db_connection

def apply_schema():
    print("Applying performance schema update...")
    conn = get_db_connection()
    cur = conn.cursor()
    
    sql_file = os.path.join(os.path.dirname(__file__), 'db', 'update_schema_performance.sql')
    
    with open(sql_file, 'r') as f:
        sql = f.read()
        
    try:
        cur.execute(sql)
        conn.commit()
        print("Schema applied successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error applying schema: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    apply_schema()
