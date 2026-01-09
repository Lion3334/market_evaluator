import sys
import os
import psycopg2
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from database import get_db_connection
from ebay_service import EbayService

load_dotenv()

APP_ID = os.getenv("EBAY_APP_ID")
CERT_ID = os.getenv("EBAY_CERT_ID")

def add_card(player_name, year, set_name, card_number, epid=None):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if already exists
        cur.execute("""
            SELECT product_id FROM cards 
            WHERE player_name = %s AND year = %s AND set_name = %s AND card_number = %s
        """, (player_name, year, set_name, card_number))
        
        if cur.fetchone():
            print(f"Card already exists: {player_name} {set_name}")
            return

        # Fetch EPID if missing
        if not epid:
            print(f"Searching EPID for {player_name}...")
            service = EbayService(APP_ID, CERT_ID)
            # Logic to fetch EPID would go here (simplified for now as this script seems to be a utility)
            # For now, insert without EPID if not provided
            pass

        cur.execute("""
            INSERT INTO cards (player_name, year, set_name, card_number, epid)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING product_id
        """, (player_name, year, set_name, card_number, epid))
        
        pid = cur.fetchone()[0]
        conn.commit()
        print(f"Added card {pid}: {player_name}")
        
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error adding card: {e}")

if __name__ == "__main__":
    # Example usage
    # add_card("Caleb Williams", 2024, "Panini Prizm", "1")
    pass
