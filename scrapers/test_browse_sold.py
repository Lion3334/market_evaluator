import httpx
import os
from ebay_service import EbayService

APP_ID = os.getenv("EBAY_APP_ID")
CERT_ID = os.getenv("EBAY_CERT_ID")

# 1. Standard Browse API
BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
# 2. Marketplace Insights API (Restricted)
INSIGHTS_URL = "https://api.ebay.com/buy/marketplace_insights/v1/item_sales/search"

def test_browse_api():
    service = EbayService(APP_ID, CERT_ID)
    token = service.get_token()
    print(f"Token: {token[:10]}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
    }
    
    # Attempt 1: Browse API with filters?
    # Trying to see if we can find 'COMPLETED' or something similar.
    # Note: Browse API mostly for live items.
    print("\n[Test 1] Browse API (item_summary/search)...")
    params = {
        "q": "Drake Maye Downtown",
        "limit": 5
    }
    try:
        resp = httpx.get(BROWSE_URL, headers=headers, params=params)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('itemSummaries', [])
            print(f"Found {len(items)} active items.")
            if items:
                print(f"Sample: {items[0].get('title')}")
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

    # Attempt 2: Marketplace Insights API (The 'correct' way for sold data in new stack)
    print("\n[Test 2] Marketplace Insights API (item_sales/search)...")
    params = {
        "q": "Drake Maye Downtown",
        "limit": 5
    }
    try:
        resp = httpx.get(INSIGHTS_URL, headers=headers, params=params)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("Success! Marketplace Insights is enabled.")
            print(resp.json())
        else:
            print(f"Failed. (Likely restricted access): {resp.status_code}")
            print(resp.text)
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_browse_api()
