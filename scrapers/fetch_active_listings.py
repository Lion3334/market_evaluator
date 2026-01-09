import sys
import os
# Add backend directory to path to import database
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import httpx
import json
import psycopg2
import re
import statistics
from datetime import datetime
from ebay_service import EbayService
from database import get_db_connection
from dotenv import load_dotenv

load_dotenv()

# Use environment variables for API credentials
APP_ID = os.getenv("EBAY_APP_ID")
CERT_ID = os.getenv("EBAY_CERT_ID")
BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

def get_variant_map():
    # Load all variants into memory for quick lookup
    # Key: (player, year, set, subset, grader, grade) -> product_id
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Variant Map - ALL cards, keyed by identifying info + grade
    variant_map = {}
    cur.execute("SELECT product_id, player_name, year, set_name, subset_insert, grader, grade FROM cards")
    for row in cur.fetchall():
        pid, player, year, set_name, subset, g, gr = row
        # Normalize keys
        key = (player, year, set_name, subset, g if g else 'Raw', gr if gr else 'Raw')
        variant_map[key] = pid
        
    # 2. Search Targets - ALL unique card bases (1 per player/year/set/subset combo)
    cur.execute("""
        SELECT DISTINCT ON (player_name, year, set_name, subset_insert) 
            epid, player_name, year, set_name, subset_insert, card_number 
        FROM cards
    """)
    search_targets = cur.fetchall()
    
    conn.close()
    return variant_map, search_targets

def parse_grade_from_title(title):
    t = title.lower()
    
    # Grader Detection
    grader = "Raw"
    grade = "Raw"
    
    # Common Grading Companies
    graders = ['psa', 'bgs', 'sgc', 'cgc', 'tag']
    
    found_grader = None
    for g in graders:
        if g in t:
            found_grader = g.upper()
            break
            
    if found_grader:
        grader = found_grader
        
        # Grade Detection (Look for numbers near the grader)
        # Regex for "PSA 10", "PSA 9.5", "SGC 10", etc.
        # Handling space or no space? usually space.
        match = re.search(rf'{found_grader.lower()}\s*(\d+(\.\d+)?)', t)
        if match:
            val = float(match.group(1))
            
            # Map to Schema Buckets
            if val == 10:
                grade = "10"
            elif val == 9:
                grade = "9"
            elif val < 9:
                grade = "<9"
            else:
                grade = "<9" # e.g. 9.5 falls into bucket? Or do we treat 9.5 as 10? 
                pass
        else:
            # Found grader but no number? Treat as "Authenticated" or Raw variant?
            # Or just default to Raw for safety if we can't pin the grade.
            pass
            
    return grader, grade

def build_query(curr_year, player, set_name, subset):
    # Construct keyword search
    # e.g. "2024 Drake Maye Panini Donruss Downtown"
    parts = [str(curr_year), player, set_name]
    if subset and subset.lower() != 'none':
        parts.append(subset)
        
    # Negative Keywords (Standard noise filter)
    negatives = "-reprint -digital -break -razz -image"
    
    return f"{' '.join(parts)} {negatives}"

def fetch_active_for_card(query, max_pages=1):
    """Fetch active listings with pagination. Default 1 page = 200 results (sufficient for daily sync)."""
    service = EbayService(APP_ID, CERT_ID)
    token = service.get_token()
    if not token:
        print("[!] No Token")
        return []

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
    }

    results = []
    
    try:
        with httpx.Client(timeout=30.0) as client:
            for page in range(max_pages):
                offset = page * 200
                
                params = {
                    "q": query,
                    "limit": 200,
                    "offset": offset,
                    "sort": "newlyListed",  # Newest first for incremental sync
                    "filter": "priceCurrency:USD"
                }
                
                resp = client.get(BROWSE_URL, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
                items = data.get('itemSummaries', [])
                
                if not items:
                    break  # No more results
                
                for item in items:
                    # 1. Location Filter (US Only)
                    location = item.get('itemLocation', {})
                    if location.get('country') != 'US':
                        continue

                    # 2. Extract Requested Fields
                    parsed = {
                        'itemId': item.get('itemId'),
                        'title': item.get('title'),
                        'legacyItemId': item.get('legacyItemId'),
                        'itemWebUrl': item.get('itemWebUrl'),
                        'price': float(item.get('price', {}).get('value', 0)),
                        'currency': item.get('price', {}).get('currency'),
                        'buyingOptions': item.get('buyingOptions', []),
                        'priorityListing': item.get('priorityListing', False),
                        'imageUrl': item.get('image', {}).get('imageUrl'),
                        'itemLocation': location,
                        'itemCreationDate': item.get('itemCreationDate'),
                        'itemOriginDate': item.get('itemOriginDate'),
                        'itemEndDate': item.get('itemEndDate'),
                        'epid': item.get('epid')  # Extract EPID for backfill
                    }
                    
                    results.append(parsed)
                    
    except Exception as e:
        print(f"Error fetching {query}: {e}")
        
    return results

def save_active_listings():
    variant_map, search_targets = get_variant_map()
    print(f"Loaded {len(variant_map)} variants and {len(search_targets)} search targets.")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    for target in search_targets:
        epid, player, year, set_name, subset, card_num = target
        query = build_query(year, player, set_name, subset)
        
        print(f"Fetching: {query}...")
        listings = fetch_active_for_card(query)
        print(f"  Found {len(listings)} items.")
        
        # Pre-calc Outliers
        if not listings: continue
        
        batch_prices = [x['price'] for x in listings]
        median_price = statistics.median(batch_prices) if batch_prices else 0
        
        # EPID Backfill: If our card is missing EPID, try to extract from listings
        if not epid:
            for item in listings:
                found_epid = item.get('epid')
                if found_epid:
                    print(f"  [EPID Backfill] Found EPID {found_epid} for {player}")
                    cur.execute("""
                        UPDATE cards SET epid = %s 
                        WHERE player_name = %s AND year = %s AND set_name = %s 
                        AND subset_insert = %s AND epid IS NULL
                    """, (found_epid, player, year, set_name, subset))
                    epid = found_epid  # Update local reference
                    break
        
        inserted_cnt = 0
        
        for item in listings:
            # 1. Parse Variant
            grader, grade = parse_grade_from_title(item['title'])
            
            # 2. Map to Product ID
            # Look up: (player, year, set, subset, grader, grade)
            key = (player, year, set_name, subset, grader, grade)
            product_id = variant_map.get(key)
            
            # If "Chase" keyword in title -> Ignore
            is_ignored = False
            title_lower = item['title'].lower()
            if any(x in title_lower for x in ['chase', 'razz', 'break', 'digital']):
                is_ignored = True
                
            # 3. Price Outlier Check
            # Check against global median for search (< 25%)
            if item['price'] < (median_price * 0.25):
                is_ignored = True
                
            # DB Insert
            try:
                cur.execute("""
                    INSERT INTO active_listings (
                        item_id, legacy_item_id, title, price, currency, 
                        buying_options, listing_url, image_url, item_location, 
                        priority_listing, start_date, end_date, origin_date, search_query, 
                        updated_at, grader, grade, product_id, is_ignored
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s)
                    ON CONFLICT (item_id) 
                    DO UPDATE SET
                        price = EXCLUDED.price,
                        updated_at = CURRENT_TIMESTAMP,
                        grader = EXCLUDED.grader,
                        grade = EXCLUDED.grade,
                        product_id = EXCLUDED.product_id,
                        is_ignored = EXCLUDED.is_ignored;
                """, (
                    item['itemId'], item['legacyItemId'], item['title'], item['price'], item['currency'],
                    ",".join(item['buyingOptions']), item['itemWebUrl'], item['imageUrl'], json.dumps(item['itemLocation']),
                    item['priorityListing'], item['itemCreationDate'], item['itemEndDate'], item['itemOriginDate'], query,
                    grader, grade, product_id, is_ignored
                ))
                inserted_cnt += 1
            except Exception as e:
                print(f"    Error inserting {item['itemId']}: {e}")

        conn.commit()
    
    cur.close()
    conn.close()
    print("Full Sync Complete.")

if __name__ == "__main__":
    save_active_listings()
