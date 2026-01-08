import httpx
import psycopg2
import re
from datetime import datetime
from ebay_service import EbayService

# Finding API
import os

# Finding API
FINDING_URL = "https://svcs.ebay.com/services/search/FindingService/v1"
APP_ID = os.getenv("EBAY_APP_ID")
CERT_ID = os.getenv("EBAY_CERT_ID")

def get_db_connection():
    return psycopg2.connect(database="cardpulse")

def fetch_completed_sales(epid, query):
    """Fetch sold listings for an EPID using Finding API (Keyword Search)"""
    service = EbayService(APP_ID, CERT_ID)
    token = service.get_token()
    
    if not token:
        print(" [!] No Token")
        return []

    headers = {
        "X-EBAY-SOA-OPERATION-NAME": "findCompletedItems",
        "X-EBAY-SOA-SECURITY-APPNAME": APP_ID,
        "X-EBAY-SOA-RESPONSE-DATA-FORMAT": "JSON",
        "X-EBAY-SOA-GLOBAL-ID": "EBAY-US",
        "X-EBAY-API-IAF-TOKEN": token
    }
    
    # Use Keyword search (more reliable than productId in legacy API)
    params = {
        "keywords": query,
        "itemFilter(0).name": "SoldItemsOnly",
        "itemFilter(0).value": "true",
        "sortOrder": "EndTimeSoonest",
        "paginationInput.entriesPerPage": "100"
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(FINDING_URL, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            resp = data.get('findCompletedItemsResponse', [{}])[0]
            if 'errorMessage' in resp:
                # Fallback to keyword search if EPID search fails (common if EPID not in Finding API index)
                # We need to look up keywords for this EPID from DB? 
                # For now return empty or handle gracefully.
                print(f"   [!] API Error: {resp['errorMessage'][0].get('error', [{}])[0].get('message')}")
                return []
                
            search_result = resp.get('searchResult', [{}])[0]
            items = search_result.get('item', [])
            return items
            
    except Exception as e:
        print(f"   [!] Http Error: {e}")
        return []

def parse_grade(title):
    t = title.lower()
    
    # Grader
    if "psa" in t:
        grader = "PSA"
        # Grade
        if "psa 10" in t or "psa 10" in t.replace("  ", " "):
            grade = "10"
        elif "psa 9" in t:
            grade = "9"
        else:
            # Check for other numbers?
            # User schema: PSA <9
            # Verify if it's actually graded using regex
            match = re.search(r'psa\s*(\d+)', t)
            if match:
                val = int(match.group(1))
                if val < 9:
                    grade = "<9"
                else:
                    # e.g. PSA 8.5? PSA 9.5?
                    grade = "<9" # Bucket anything else into here for now or ignore?
                    # logic: 10->10, 9->9, else-><9
            else:
                return "Raw", "Raw" # Mentioned PSA but no grade? Assume Raw/Authenticated?
    else:
        grader = "Raw"
        grade = "Raw"
        
    return grader, grade

def update_sales():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Get Distinct EPIDs to update (and metadata for query)
    # We only need to search ONCE per EPID.
    # So let's select DISTINCT ON (epid) ...
    cur.execute("SELECT DISTINCT ON (epid) epid, player_name, year, set_name, subset_insert, card_number FROM cards WHERE epid IS NOT NULL AND epid != 'none'")
    
    rows = cur.fetchall()
    print(f"Found {len(rows)} distinct EPIDs to scan.")
    
    # 2. Pre-fetch Variant Map for quick lookup
    # Map: (epid, grader, grade) -> product_id
    variant_map = {}
    cur.execute("SELECT product_id, epid, grader, grade FROM cards WHERE epid IS NOT NULL")
    for row in cur.fetchall():
        pid, ep, g, gr = row
        variant_map[(ep, g, gr)] = pid
        
    for row in rows:
        epid, player, year, set_name, subset, card_num = row
        # Construct query: e.g. "2024 Drake Maye Panini Donruss Downtown #13"
        # If subset is 'Downtown', usually that's key. 
        if subset and subset != 'none':
             query = f"{year} {player} {set_name} {subset}"
        else:
             query = f"{year} {player} {set_name} #{card_num}"
             
        print(f"Scanning EPID {epid} ({query})...")
        items = fetch_completed_sales(epid, query)
        print(f"   Found {len(items)} raw listings.")
        
        count_inserted = 0
        for item in items:
            title = item.get('title', [''])[0]
            selling_status = item.get('sellingStatus', [{}])[0]
            price_val = selling_status.get('currentPrice', [{}])[0].get('__value__', 0)
            price = float(price_val)
            
            date_str = item.get('listingInfo', [{}])[0].get('endTime', [''])[0]
            try:
                sale_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                sale_date = datetime.now()
                
            grader, grade = parse_grade(title)
            
            # Lookup Product ID
            # Our parser output: ('PSA', '10'), ('PSA', '9'), ('PSA', '<9'), ('Raw', 'Raw')
            # Check if this variant exists in our map
            
            product_id = variant_map.get((epid, grader, grade))
            
            if not product_id:
                # If we parsed 'PSA 8' -> grader='PSA', grade='<9', verify map has it
                # If parsed 'PSA 10' but map missing? Skip.
                # print(f"      Skipping variant: {grader} {grade} (Not in DB)")
                continue
                
            # Insert into sales
            txn_id = item.get('itemId', [''])[0]
            
            # Note: Postgres Schema v2 'sales' columns:
            # transaction_id, product_id, price, sale_date, grader, grade, source, title
            
            try:
                cur.execute("""
                    INSERT INTO sales (transaction_id, product_id, price, sale_date, grader, grade, source, title)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (transaction_id, source) DO NOTHING
                """, (txn_id, product_id, price, sale_date, grader, grade, 'eBay', title))
                count_inserted += 1
            except Exception as e:
                print(f"      DB Error: {e}")
                conn.rollback()
                
        conn.commit()
        print(f"   Indexed {count_inserted} sales.")
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    update_sales()
