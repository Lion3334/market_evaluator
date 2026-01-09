import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        # Fallback to local if no URL is set (safety net)
        print("Warning: DATABASE_URL not found, using local 'cardpulse'.")
        return psycopg2.connect(database="cardpulse")
    
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"Connection Error: {e}")
        raise e

if __name__ == "__main__":
    try:
        conn = get_db_connection()
        print("Successfully connected to Supabase!")
        conn.close()
    except:
        print("Failed to connect.")
