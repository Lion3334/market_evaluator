import psycopg2
import os

def init_db():
    conn = None
    try:
        # Connect to the database
        conn = psycopg2.connect(
            database="cardpulse",
            # Assuming default local user config relies on socket, or user is 'eastcoastlimited' based on machine
            # We try with minimal args first, as often default config works for socket
        )
        cur = conn.cursor()
        
        # Read schema file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(script_dir, "schema.sql")
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
            
        print("Executing schema...")
        cur.execute(schema_sql)
        conn.commit()
        print("Database initialized successfully!")
        
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    init_db()
