"""
Set-Level Active Listings Fetcher
Queries eBay by SET name, paginates, and parses titles to assign product_id.
"""
import sys
import os
import json
import re
import httpx
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from database import get_db_connection
from ebay_service import EbayService
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("EBAY_APP_ID")
CERT_ID = os.getenv("EBAY_CERT_ID")
BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

def get_product_lookup(set_name):
    """
    Build a lookup map from (player_name, card_number, grader, grade) -> product_id
    for a specific set.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    lookup = {}
    cur.execute("""
        SELECT product_id, player_name, card_number, grader, grade 
        FROM cards WHERE set_name = %s
    """, (set_name,))
    
    for row in cur.fetchall():
        pid, player, card_num, grader, grade = row
        # Normalize
        player_lower = player.lower().strip() if player else ""
        card_num_clean = str(card_num).strip() if card_num else ""
        grader = grader if grader else "Raw"
        grade = grade if grade else "Raw"
        
        key = (player_lower, card_num_clean, grader, grade)
        lookup[key] = pid
    
    cur.close()
    conn.close()
    return lookup

def get_existing_item_ids():
    """Return set of item_ids already in active_listings for duplicate detection."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT item_id FROM active_listings")
    existing = {row[0] for row in cur.fetchall()}
    cur.close()
    conn.close()
    return existing

def parse_grade_from_title(title):
    """Extract grader and grade from title."""
    t = title.lower()
    grader = "Raw"
    grade = "Raw"
    
    graders = ['psa', 'bgs', 'sgc', 'cgc']
    for g in graders:
        if g in t:
            grader = g.upper()
            match = re.search(rf'{g}\s*(\d+(\.\d+)?)', t)
            if match:
                val = float(match.group(1))
                if val == 10:
                    grade = "10"
                elif val == 9:
                    grade = "9"
                else:
                    grade = "<9"
            break
    return grader, grade

def parse_player_and_number(title, known_players):
    """
    Extract player name and card number from title.
    Returns (player_name, card_number) or (None, None) if not found.
    """
    # Normalize: Remove periods, apostrophes for matching
    def normalize(s):
        return re.sub(r"[.']", "", s.lower())
    
    title_norm = normalize(title)
    
    # Card Number: Look for #XX pattern
    card_num_match = re.search(r'#(\d+)', title)
    card_num = card_num_match.group(1) if card_num_match else None
    
    # Player: Check against known players (longest match first)
    found_player = None
    for player in sorted(known_players, key=len, reverse=True):
        player_norm = normalize(player)
        if player_norm in title_norm:
            found_player = player
            break
    
    return found_player, card_num

def fetch_set_listings(set_query, max_pages=100, stop_on_duplicate=True):
    """
    Fetch all active listings for a set.
    Stops when we hit duplicates (incremental sync) or max_pages.
    """
    service = EbayService(APP_ID, CERT_ID)
    token = service.get_token()
    if not token:
        print("[!] No Token")
        return []
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
    }
    
    existing_ids = get_existing_item_ids() if stop_on_duplicate else set()
    results = []
    duplicates_found = 0
    
    try:
        with httpx.Client(timeout=30.0) as client:
            for page in range(max_pages):
                offset = page * 200
                
                params = {
                    "q": f"{set_query} -reprint -digital -break -razz -image",
                    "limit": 200,
                    "offset": offset,
                    "sort": "newlyListed",
                    "filter": "priceCurrency:USD"
                }
                
                print(f"Fetching page {page + 1} (offset={offset})...")
                resp = client.get(BROWSE_URL, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
                items = data.get('itemSummaries', [])
                
                if not items:
                    print("  No more items. End of results.")
                    break
                
                page_duplicates = 0
                for item in items:
                    item_id = item.get('itemId')
                    
                    # Duplicate check
                    if item_id in existing_ids:
                        page_duplicates += 1
                        continue
                    
                    # Location filter (US only)
                    location = item.get('itemLocation', {})
                    if location.get('country') != 'US':
                        continue
                    
                    parsed = {
                        'itemId': item_id,
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
                        'epid': item.get('epid')
                    }
                    results.append(parsed)
                
                print(f"  Found {len(items)} items, {page_duplicates} duplicates, {len(items) - page_duplicates} new.")
                
                # Stop condition: If more than 50% of page is duplicates, we've caught up
                if stop_on_duplicate and page_duplicates > len(items) * 0.5:
                    print("  High duplicate rate. Stopping incremental sync.")
                    break
                    
    except Exception as e:
        print(f"Error fetching: {e}")
    
    return results

def save_listings_for_set(set_name, set_query):
    """Main function to fetch and save listings for a set with grade-specific queries."""
    print(f"\n{'='*60}")
    print(f"Fetching Active Listings for: {set_name}")
    print(f"{'='*60}\n")
    
    # 1. Build lookup
    lookup = get_product_lookup(set_name)
    known_players = list(set(k[0] for k in lookup.keys()))
    print(f"Loaded {len(lookup)} product variants and {len(known_players)} unique players.")
    
    # 2. Define grade-specific queries
    grade_queries = [
        (f"{set_query} -PSA -BGS -SGC -CGC", "Raw", "Raw"),  # Ungraded
        (f"{set_query} PSA 10", "PSA", "10"),
        (f"{set_query} PSA 9", "PSA", "9"),
        (f"{set_query} PSA 8", "PSA", "<9"),  # PSA 8 and below -> <9 bucket
    ]
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    total_matched = 0
    total_unmatched = 0
    total_processed = 0
    
    for query, grader, grade in grade_queries:
        print(f"\n--- Querying: {query} ---")
        listings = fetch_set_listings(query)
        print(f"Fetched {len(listings)} new listings.")
        
        if not listings:
            continue
        
        matched = 0
        unmatched = 0
        
        for item in listings:
            title = item['title']
            player, card_num = parse_player_and_number(title, known_players)
            
            # Use grade from query context (more reliable than title parsing)
            product_id = None
            if player and card_num:
                key = (player.lower(), card_num, grader, grade)
                product_id = lookup.get(key)
            
            if product_id:
                matched += 1
            else:
                unmatched += 1
            
            # Exclusion logic
            is_ignored = False
            title_lower = title.lower()
            if any(x in title_lower for x in ['chase', 'razz', 'break', 'digital', 'lot of']):
                is_ignored = True
            
            try:
                cur.execute("""
                    INSERT INTO active_listings (
                        item_id, legacy_item_id, title, price, currency, 
                        buying_options, listing_url, image_url, item_location, 
                        priority_listing, start_date, end_date, origin_date, search_query, 
                        updated_at, grader, grade, product_id, is_ignored
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s)
                    ON CONFLICT (item_id) DO UPDATE SET
                        price = EXCLUDED.price,
                        updated_at = CURRENT_TIMESTAMP,
                        grader = EXCLUDED.grader,
                        grade = EXCLUDED.grade,
                        product_id = EXCLUDED.product_id,
                        is_ignored = EXCLUDED.is_ignored;
                """, (
                    item['itemId'], item['legacyItemId'], title, item['price'], item['currency'],
                    ",".join(item['buyingOptions']), item['itemWebUrl'], item['imageUrl'], 
                    json.dumps(item['itemLocation']),
                    item['priorityListing'], item['itemCreationDate'], item['itemEndDate'], 
                    item['itemOriginDate'], query,
                    grader, grade, product_id, is_ignored
                ))
            except Exception as e:
                print(f"Error inserting {item['itemId']}: {e}")
        
        conn.commit()
        print(f"  Matched: {matched}, Unmatched: {unmatched}")
        total_matched += matched
        total_unmatched += unmatched
        total_processed += len(listings)
    
    cur.close()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"SUMMARY for {set_name}")
    print(f"{'='*60}")
    print(f"Total Processed: {total_processed}")
    print(f"Matched to Product: {total_matched} ({total_matched/max(total_processed,1)*100:.1f}%)")
    print(f"Unmatched: {total_unmatched}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    # Example: Sync 2023 Panini Illusions
    save_listings_for_set(
        set_name="Panini Illusions",
        set_query="2023 Panini Illusions"
    )
