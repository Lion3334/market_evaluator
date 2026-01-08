import sys
import os
import psycopg2
from ebay_service import EbayService

# Hardcoded for MVP (should be env vars)
APP_ID = os.getenv("EBAY_APP_ID")
CERT_ID = os.getenv("EBAY_CERT_ID")

def add_card(player, year, set_name, variant):
    query = f"{year} {player} {set_name} {variant}"
    print(f"Searching for: {query}")
    
    service = EbayService(APP_ID, CERT_ID)
    epid, title = service.find_best_epid(query)
    
    if not epid:
        print("No EPID found for this card.")
        return

    print(f"Found EPID: {epid}")
    print(f"Sample Title: {title}")
    
    confirm = input("Add to database? (y/n): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return

    try:
        conn = psycopg2.connect(database="cardpulse")
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO cards (epid, player_name, year, set_name, variant, url)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (epid) DO NOTHING
        """, (epid, player, year, set_name, variant, f"https://www.ebay.com/itm/EPID{epid}"))
        
        conn.commit()
        print("Card added successfully.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    # Example Usage: python3 add_card.py "Drake Maye" 2024 "Donruss Optic" "Rookie Kings"
    if len(sys.argv) < 5:
        print("Usage: python3 add_card.py <player> <year> <set> <variant>")
        sys.exit(1)
        
    add_card(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
