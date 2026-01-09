import os
import httpx
import json
from ebay_service import EbayService
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Use environment variables for credentials
APP_ID = os.getenv("EBAY_APP_ID")
CERT_ID = os.getenv("EBAY_CERT_ID")
BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

def inspect_epid(epid):
    print(f"Inspecting Active Listings for EPID: {epid}")
    
    service = EbayService(APP_ID, CERT_ID)
    token = service.get_token()
    
    if not token:
        print("[!] Failed to get OAuth token.")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        "Content-Type": "application/json"
    }
    
    # Searching by EPID directly often fails if no exact match on keyword index.
    # Let's try searching for a known active card to show the User the Schema.
    params = {
        "q": "Drake Maye Downtown", 
        "limit": 3
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(BROWSE_URL, headers=headers, params=params)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                total = data.get('total', 0)
                items = data.get('itemSummaries', [])
                
                print(f"Total Matches: {total}")
                print(f"Items Returned: {len(items)}")
                
                if items:
                    print("\n--- JSON Structure of First Item ---")
                    print(json.dumps(items[0], indent=2))
                    
                    print("\n--- Available Fields (Keys) ---")
                    print(list(items[0].keys()))
                else:
                    print("No items found.")
            else:
                print(f"Error: {response.text}")
                
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    inspect_epid("7073771773")
