
from database import get_db_connection

def inspect_schema():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check constraints on cards table
    print("Checking constraints on 'cards' table...")
    cur.execute("""
        SELECT conname, contype, pg_get_constraintdef(oid) 
        FROM pg_constraint 
        WHERE conrelid = 'cards'::regclass;
    """)
    constraints = cur.fetchall()
    for c in constraints:
        print(f"Constraint: {c}")
        
    # Check indexes
    print("\nChecking indexes on 'cards' table...")
    cur.execute("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'cards';
    """)
    indexes = cur.fetchall()
    for i in indexes:
        print(f"Index: {i}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    inspect_schema()
