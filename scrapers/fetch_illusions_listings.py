import sys
import os
import json
import statistics
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.append(os.path.dirname(__file__))

from database import get_db_connection
from fetch_active_listings import fetch_active_for_card, parse_grade_from_title, build_query

def sync_illusions():
    print("Starting targeted sync for '2023 Panini Illusions'...")
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Load Variants for Panini Illusions ONLY
    # This optimization prevents loading 10k+ unrelated variants (though logic is redundant if we filtered properly)
    # Actually, we need the map to look up product_ids for the inserts.
    variant_map = {}
    cur.execute("SELECT product_id, player_name, year, set_name, subset_insert, grader, grade FROM cards WHERE set_name = 'Panini Illusions'")
    for row in cur.fetchall():
        pid, player, year, set_name, subset, g, gr = row
        key = (player, year, set_name, subset, g if g else 'Raw', gr if gr else 'Raw')
        variant_map[key] = pid

    # 2. Search Targets
    cur.execute("""
        SELECT DISTINCT ON (player_name, year, set_name, subset_insert) 
            epid, player_name, year, set_name, subset_insert, card_number 
        FROM cards 
        WHERE set_name = 'Panini Illusions' AND year = 2023
    """)
    search_targets = cur.fetchall()
    
    print(f"Found {len(search_targets)} unique cards to sync.")

    for target in search_targets:
        epid, player, year, set_name, subset, card_num = target
        query = build_query(year, player, set_name, subset)
        
        print(f"Fetching: {query}...")
        listings = fetch_active_for_card(query)
        print(f"  Found {len(listings)} items.")
        
        if not listings: continue
        
        batch_prices = [x['price'] for x in listings]
        median_price = statistics.median(batch_prices) if batch_prices else 0
        
        # EPID Backfill
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
                    conn.commit()
                    break
        
        # Insert Listings
        inserted_cnt = 0
        for item in listings:
            grader, grade = parse_grade_from_title(item['title'])
            
            # Map to Product ID
            key = (player, year, set_name, subset, grader, grade)
            product_id = variant_map.get(key)
            
            # Exclusion Logic
            is_ignored = False
            title_lower = item['title'].lower()
            if any(x in title_lower for x in ['chase', 'razz', 'break', 'digital']):
                is_ignored = True
            
            # Price Outlier (< 25% median)
            if item['price'] < (median_price * 0.25):
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
        # Polite delay not needed for API but good practice if looping tight? 
        # API handles rate limits.
    
    cur.close()
    conn.close()
    print("Sync Complete.")

if __name__ == "__main__":
    sync_illusions()
