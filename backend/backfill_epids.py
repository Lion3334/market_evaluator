import psycopg2
import sys
import os

# Adjust path to find modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scrapers')))
from ebay_service import EbayService

# Credentials (from existing scripts)
# Credentials (from existing scripts)
APP_ID = os.getenv("EBAY_APP_ID")
CERT_ID = os.getenv("EBAY_CERT_ID")

def populate_epids():
    conn = psycopg2.connect(database="cardpulse")
    cur = conn.cursor()
    
    # Init service
    ebay = EbayService(APP_ID, CERT_ID)
    
    # 1. Find cards with missing EPIDs
    print("Finding cards with missing EPIDs...")
    cur.execute("""
        SELECT product_id, player_name, year, set_name, card_number
        FROM cards
        WHERE epid IS NULL OR epid = 'none' OR epid = 'MISSING';
    """)
    rows = cur.fetchall()
    print(f"Found {len(rows)} cards needing EPID.")
    
    updated_count = 0
    
    for row in rows:
        pid, player, year, set_name, card_num = row
        query = f"{year} {player} {set_name} {card_num}"
        print(f"Searching for: {query}...")
        
        try:
            best_epid, title = ebay.find_best_epid(query)
            
            if best_epid:
                print(f"  -> Found EPID: {best_epid} ({title[:30]}...)")
                cur.execute("UPDATE cards SET epid = %s WHERE product_id = %s", (best_epid, pid))
                updated_count += 1
            else:
                print("  -> No EPID found.")
        except Exception as e:
            print(f"  -> API Error: {e}")
            
    conn.commit()
    conn.close()
    print(f"Update complete. Updated {updated_count} cards.")

if __name__ == "__main__":
    populate_epids()
