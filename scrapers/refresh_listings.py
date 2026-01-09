"""
Refresh Listings Script

Orchestrates the tiered refresh of eBay listings:
1. Queries cards where next_refresh_due <= TODAY
2. For each card, fetches current listings from eBay API
3. Compares with stored active_listings:
   - New listings: INSERT
   - Existing listings: UPDATE last_seen_at
   - Disappeared listings: Mark is_active=FALSE, set disappeared_at
4. Updates last_refreshed_at and calculates next_refresh_due
"""

import os
import sys
import time
import requests
from datetime import date, datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import get_db_connection

load_dotenv()

# Tier refresh intervals (days)
TIER_INTERVALS = {
    1: 1,   # Daily
    2: 2,   # Every 2 days
    3: 4,   # Every 4 days
    4: 7,   # Weekly
}

# eBay API config
EBAY_APP_ID = os.getenv('EBAY_APP_ID')
EBAY_ACCESS_TOKEN = os.getenv('EBAY_ACCESS_TOKEN')

def get_cards_due_for_refresh(conn):
    """Get cards where next_refresh_due <= today"""
    cur = conn.cursor()
    query = """
        SELECT product_id, epid, refresh_tier
        FROM cards
        WHERE next_refresh_due <= %s
        AND epid IS NOT NULL
        ORDER BY refresh_tier ASC, next_refresh_due ASC
        LIMIT 500
    """
    cur.execute(query, (date.today(),))
    cards = cur.fetchall()
    cur.close()
    return cards

def fetch_ebay_listings_by_epid(epid):
    """Fetch current active listings from eBay Browse API by EPID"""
    if not EBAY_ACCESS_TOKEN:
        print("Warning: No EBAY_ACCESS_TOKEN configured")
        return []
    
    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    headers = {
        "Authorization": f"Bearer {EBAY_ACCESS_TOKEN}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
    }
    params = {
        "epid": epid,
        "limit": 200
    }
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('itemSummaries', [])
        else:
            print(f"  eBay API error: {resp.status_code}")
            return []
    except Exception as e:
        print(f"  eBay API exception: {e}")
        return []

def process_card_refresh(conn, product_id, epid, tier):
    """Process refresh for a single card"""
    cur = conn.cursor()
    now = datetime.now()
    today = date.today()
    
    # 1. Get current active listings from our DB
    cur.execute("""
        SELECT item_id FROM active_listings 
        WHERE product_id = %s AND is_active = TRUE
    """, (product_id,))
    db_item_ids = set(row[0] for row in cur.fetchall())
    
    # 2. Fetch current listings from eBay
    ebay_listings = fetch_ebay_listings_by_epid(epid)
    ebay_item_ids = set(item.get('itemId') for item in ebay_listings if item.get('itemId'))
    
    # 3. Find new, existing, and disappeared
    new_ids = ebay_item_ids - db_item_ids
    existing_ids = ebay_item_ids & db_item_ids
    disappeared_ids = db_item_ids - ebay_item_ids
    
    # 4. Insert new listings
    for item in ebay_listings:
        item_id = item.get('itemId')
        if item_id in new_ids:
            price_val = item.get('price', {}).get('value', 0)
            title = item.get('title', '')[:255]
            listing_type = 'FIXED_PRICE' if item.get('buyingOptions') and 'FIXED_PRICE' in item.get('buyingOptions', []) else 'AUCTION'
            
            cur.execute("""
                INSERT INTO active_listings (product_id, item_id, price, title, listing_type, last_seen_at, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                ON CONFLICT (item_id) DO UPDATE SET last_seen_at = %s, is_active = TRUE
            """, (product_id, item_id, price_val, title, listing_type, now, now))
    
    # 5. Update last_seen_at for existing
    if existing_ids:
        cur.execute("""
            UPDATE active_listings 
            SET last_seen_at = %s 
            WHERE item_id = ANY(%s)
        """, (now, list(existing_ids)))
    
    # 6. Mark disappeared listings
    if disappeared_ids:
        cur.execute("""
            UPDATE active_listings 
            SET is_active = FALSE, disappeared_at = %s 
            WHERE item_id = ANY(%s) AND is_active = TRUE
        """, (now, list(disappeared_ids)))
    
    # 7. Update card refresh timestamps
    next_refresh = today + timedelta(days=TIER_INTERVALS.get(tier, 7))
    cur.execute("""
        UPDATE cards 
        SET last_refreshed_at = %s, next_refresh_due = %s
        WHERE product_id = %s
    """, (now, next_refresh, product_id))
    
    conn.commit()
    cur.close()
    
    return len(new_ids), len(disappeared_ids)

def refresh_listings():
    """Main refresh orchestration"""
    print(f"Starting tiered refresh at {datetime.now()}")
    conn = get_db_connection()
    
    cards = get_cards_due_for_refresh(conn)
    print(f"Found {len(cards)} cards due for refresh.")
    
    if not cards:
        print("No cards due for refresh today.")
        conn.close()
        return
    
    total_new = 0
    total_disappeared = 0
    api_calls = 0
    
    for product_id, epid, tier in cards:
        if not epid:
            continue
            
        print(f"Refreshing product {product_id} (Tier {tier}, EPID: {epid[:20]}...)")
        new_count, disappeared_count = process_card_refresh(conn, product_id, epid, tier)
        
        total_new += new_count
        total_disappeared += disappeared_count
        api_calls += 1
        
        # Rate limiting
        time.sleep(0.5)
        
        # Safety limit
        if api_calls >= 500:
            print("Reached daily API call safety limit (500)")
            break
    
    print(f"\nRefresh Complete:")
    print(f"  Cards processed: {api_calls}")
    print(f"  New listings: {total_new}")
    print(f"  Disappeared listings: {total_disappeared}")
    
    conn.close()

if __name__ == "__main__":
    refresh_listings()
