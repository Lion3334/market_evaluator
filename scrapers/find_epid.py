#!/usr/bin/env python3
"""Identify the correct EPID for Drake Maye Rookie Kings #3 Base card."""

import base64
import httpx
from collections import Counter
import os

EBAY_APP_ID = os.getenv("EBAY_APP_ID")
EBAY_CERT_ID = os.getenv("EBAY_CERT_ID")
PROD_AUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
PROD_BROWSE_URL = "https://api.ebay.com/buy/browse/v1"

def get_access_token():
    credentials = f"{EBAY_APP_ID}:{EBAY_CERT_ID}"
    auth_header = base64.b64encode(credentials.encode()).decode()
    with httpx.Client(timeout=30.0) as client:
        response = client.post(PROD_AUTH_URL,
            headers={"Authorization": f"Basic {auth_header}", "Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"})
        return response.json().get('access_token') if response.status_code == 200 else None

def analyze_epids(token, query):
    print(f"Searching for: {query}")
    with httpx.Client(timeout=30.0) as client:
        # Fetch a reasonable number of listings to get a good sample of EPIDs
        params = {"q": query, "category_ids": "212", "limit": 200}
        response = client.get(f"{PROD_BROWSE_URL}/item_summary/search",
            headers={"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"},
            params=params)
        
        if response.status_code != 200:
            print("Error searching eBay")
            return

        items = response.json().get('itemSummaries', [])
        print(f"Propagating {len(items)} listings...")

        epid_map = {} # EPID -> List of titles
        no_epid_count = 0

        for item in items:
            title = item.get('title', 'No Title')
            epid = item.get('epid')
            
            if epid:
                if epid not in epid_map:
                    epid_map[epid] = []
                epid_map[epid].append(title)
            else:
                no_epid_count += 1
        
        print(f"\nFound {len(epid_map)} unique EPIDs. ({no_epid_count} listings had no EPID)")
        
        print("\nTOP EPIDS FOUND:")
        print("-" * 80)
        # Sort by frequency
        sorted_epids = sorted(epid_map.items(), key=lambda x: len(x[1]), reverse=True)
        
        for epid, titles in sorted_epids[:5]:
            print(f"EPID: {epid} ({len(titles)} listings)")
            # Show top 3 most common titles for this EPID to judge what card it is
            common_titles = Counter(titles).most_common(3)
            for title, count in common_titles:
                print(f"   - [{count}] {title[:70]}...")
            print("")

        return sorted_epids[0][0] if sorted_epids else None

def test_epid_search(token, epid):
    print("=" * 80)
    print(f"TESTING RESTRICTED SEARCH WITH EPID: {epid}")
    print("=" * 80)
    
    with httpx.Client(timeout=30.0) as client:
        params = {"epid": epid, "limit": 50}
        response = client.get(f"{PROD_BROWSE_URL}/item_summary/search",
            headers={"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"},
            params=params)
            
        items = response.json().get('itemSummaries', [])
        print(f"Found {len(items)} listings for this EPID.")
        
        prices = []
        titles = []
        for item in items:
            price = float(item.get('price', {}).get('value', 0))
            prices.append(price)
            titles.append(f"${price:>6.2f} | {item.get('title', '')[:60]}")
            
        avg_price = sum(prices) / len(prices) if prices else 0
        
        print(f"\nAverage Price: ${avg_price:.2f}")
        print("\nSample Listings:")
        for t in sorted(titles)[:10]:
            print(t)

if __name__ == "__main__":
    token = get_access_token()
    # Broad search to find the EPID
    best_epid = analyze_epids(token, "Drake Maye Rookie Kings 2024 Donruss Optic -Primary") # exclude Primary colors if possible via simple keyword to help find the right epid
    
    if best_epid:
        test_epid_search(token, best_epid)
