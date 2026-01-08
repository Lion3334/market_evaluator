import httpx
import psycopg2
from datetime import datetime
import os
from ebay_service import EbayService

# Finding API is XML/GET based, different from Browse API
FINDING_URL = "https://svcs.ebay.com/services/search/FindingService/v1"
# Credentials (should match EbayService)
APP_ID = os.getenv("EBAY_APP_ID")
CERT_ID = os.getenv("EBAY_CERT_ID")

def fetch_completed_sales(epid, query):
    """
    Use Finding API to get sold listings using keywords, then associate with EPID.
    Uses OAuth (IAF) token to bypass public rate limits.
    """
    # Get OAuth Token
    service = EbayService(APP_ID, CERT_ID)
    token = service.get_token()
    
    if not token:
        print("Failed to generate OAuth token for Finding API.")
        return []

    headers = {
        "X-EBAY-SOA-OPERATION-NAME": "findCompletedItems",
        "X-EBAY-SOA-SECURITY-APPNAME": APP_ID,
        "X-EBAY-SOA-RESPONSE-DATA-FORMAT": "JSON",
        "X-EBAY-SOA-GLOBAL-ID": "EBAY-US",
        "X-EBAY-API-IAF-TOKEN": token
    }
    
    params = {
        "categoryId": "212", 
        "keywords": query,
        "itemFilter(0).name": "SoldItemsOnly",
        "itemFilter(0).value": "true",
        "sortOrder": "EndTimeSoonest",
        "paginationInput.entriesPerPage": "100"
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(FINDING_URL, headers=headers, params=params)
            if response.status_code != 200:
                print(f"API Error {response.status_code}: {response.text}")
            response.raise_for_status()
            data = response.json()
            
            search_result = data.get('findCompletedItemsResponse', [{}])[0].get('searchResult', [{}])[0]
            count = int(search_result.get('@count', 0))
            items = search_result.get('item', [])
            
            sales = []
            for item in items:
                listing_info = item.get('listingInfo', [{}])[0]
                selling_status = item.get('sellingStatus', [{}])[0]
                
                title = item.get('title', [''])[0]
                price_val = selling_status.get('currentPrice', [{}])[0].get('__value__', 0)
                price = float(price_val) if price_val else 0.0
                
                date_str = listing_info.get('endTime', [''])[0]
                try:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date_val = dt.date()
                except:
                    date_val = datetime.now().date()

                # Basic Grade parsing
                grade = "RAW"
                title_lower = title.lower()
                if "psa 10" in title_lower: grade = "PSA_10"
                elif "psa 9" in title_lower: grade = "PSA_9"
                elif "bgs 9.5" in title_lower: grade = "BGS_9.5"
                elif "sgc 10" in title_lower: grade = "SGC_10"
                
                sales.append({
                    'epid': epid,
                    'date': date_val,
                    'price': price,
                    'grade': grade,
                    'title': title
                })
                
            return sales
            
    except Exception as e:
        print(f"Error fetching sales for EPID {epid}: {e}")
        return []

def update_all_cards():
    try:
        conn = psycopg2.connect(database="cardpulse")
        cur = conn.cursor()
        
        # Get all cards
        cur.execute("SELECT epid, player_name, year, set_name, variant FROM cards")
        cards = cur.fetchall()
        print(f"Updating sales for {len(cards)} cards...")
        
        total_added = 0
        for epid, player, year, set_name, variant in cards:
            query = f"{year} {player} {set_name} {variant}"
            print(f"Fetching {query} (EPID: {epid})...")
            sales = fetch_completed_sales(epid, query)
            print(f"  Found {len(sales)} sales.")
            
            for s in sales:
                # Insert if not exists (simple dedupe by date+price+epid for MVP, or just insert all)
                # Ideally we rely on an external ID, but FindingAPI listingId is good
                # Let's just blindly insert for MVP pilot
                cur.execute("""
                    INSERT INTO transactions (card_epid, txn_date, price, grade, source, title)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (s['epid'], s['date'], s['price'], s['grade'], 'eBay_Finding', s['title']))
                
            conn.commit()
            total_added += len(sales)
            
        print(f"Total transactions added: {total_added}")
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    update_all_cards()
