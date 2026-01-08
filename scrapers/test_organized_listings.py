#!/usr/bin/env python3
"""Fetch and organize eBay listings with clickable links for each condition."""

import base64
import httpx
import re
from datetime import datetime
from urllib.parse import quote_plus
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


def detect_condition(title: str, condition_field: str) -> str:
    """Detect if card is Raw, PSA 9, PSA 10, etc."""
    title_lower = title.lower()
    
    if re.search(r'psa\s*10', title_lower) or 'gem mint' in title_lower:
        return 'PSA_10'
    if re.search(r'psa\s*9\b', title_lower) or 'mint 9' in title_lower:
        return 'PSA_9'
    
    psa_match = re.search(r'psa\s*(\d+)', title_lower)
    if psa_match:
        return f'PSA_{psa_match.group(1)}'
    
    if condition_field == 'Graded':
        return 'GRADED_UNKNOWN'
    
    return 'RAW'


def search_all_listings(token, query, epid=None):
    """Search for all listings."""
    with httpx.Client(timeout=30.0) as client:
        params = {"q": query, "category_ids": "212", "limit": 100}
        if epid:
            params["epid"] = epid
        
        response = client.get(f"{PROD_BROWSE_URL}/item_summary/search",
            headers={"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"},
            params=params)
        
        return response.json().get('itemSummaries', []) if response.status_code == 200 else []


def organize_listings(items):
    """Organize listings by type and condition."""
    organized = {
        'BIN': {'RAW': [], 'PSA_9': [], 'PSA_10': [], 'OTHER': []},
        'AUCTION': {'RAW': [], 'PSA_9': [], 'PSA_10': [], 'OTHER': []}
    }
    
    for item in items:
        title = item.get('title', '')
        condition = item.get('condition', '')
        price = float(item.get('price', {}).get('value', 0))
        buying_options = item.get('buyingOptions', [])
        
        listing_type = 'AUCTION' if 'AUCTION' in buying_options else 'BIN'
        card_condition = detect_condition(title, condition)
        
        bucket = 'OTHER'
        if card_condition == 'RAW':
            bucket = 'RAW'
        elif card_condition == 'PSA_9':
            bucket = 'PSA_9'
        elif card_condition == 'PSA_10':
            bucket = 'PSA_10'
        
        organized[listing_type][bucket].append({'price': price, 'title': title, 'item': item})
    
    return organized


def calculate_avg(listings):
    if not listings:
        return None
    prices = [l['price'] for l in listings if l['price'] > 0]
    return sum(prices) / len(prices) if prices else None


def generate_bin_url(query, condition_filter=None):
    """Generate eBay BIN search URL."""
    search_term = query
    if condition_filter:
        search_term = f"{query} {condition_filter}"
    
    return f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(search_term)}&_sacat=212&LH_BIN=1&rt=nc"


def generate_auction_url(query, condition_filter=None):
    """Generate eBay Auction search URL."""
    search_term = query
    if condition_filter:
        search_term = f"{query} {condition_filter}"
    
    return f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(search_term)}&_sacat=212&LH_Auction=1&rt=nc"


def main():
    print("="*90)
    print("eBay Market Data - Caleb Williams Planetary Pursuit The Sun")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*90)
    
    token = get_access_token()
    query = "Caleb Williams Planetary Pursuit Sun 2024 Topps Cosmic"
    epid = "2350717052"
    
    items = search_all_listings(token, query, epid)
    organized = organize_listings(items)
    
    # Calculate averages
    bin_raw_avg = calculate_avg(organized['BIN']['RAW'])
    bin_psa9_avg = calculate_avg(organized['BIN']['PSA_9'])
    bin_psa10_avg = calculate_avg(organized['BIN']['PSA_10'])
    
    # Generate URLs
    bin_raw_url = generate_bin_url(query)
    bin_psa9_url = generate_bin_url(query, "PSA 9")
    bin_psa10_url = generate_bin_url(query, "PSA 10")
    
    auction_raw_url = generate_auction_url(query)
    auction_psa9_url = generate_auction_url(query, "PSA 9")
    auction_psa10_url = generate_auction_url(query, "PSA 10")
    
    # Count
    bin_raw_count = len(organized['BIN']['RAW'])
    bin_psa9_count = len(organized['BIN']['PSA_9'])
    bin_psa10_count = len(organized['BIN']['PSA_10'])
    
    auction_raw_count = len(organized['AUCTION']['RAW'])
    auction_psa9_count = len(organized['AUCTION']['PSA_9'])
    auction_psa10_count = len(organized['AUCTION']['PSA_10'])
    
    print("\n" + "="*90)
    print("                              MARKET DATA DISPLAY")
    print("="*90)
    
    # BIN Section
    print("\n┌─────────────────────────────────────────────────────────────────────────────────────┐")
    print("│                                BUY IT NOW                                           │")
    print("├─────────────────────────────┬─────────────────────────────┬─────────────────────────┤")
    print("│            Raw              │           PSA 9             │          PSA 10         │")
    print("├─────────────────────────────┼─────────────────────────────┼─────────────────────────┤")
    
    # Price row
    raw_price = f"${bin_raw_avg:.2f}" if bin_raw_avg else "-"
    psa9_price = f"${bin_psa9_avg:.2f}" if bin_psa9_avg else "-"
    psa10_price = f"${bin_psa10_avg:.2f}" if bin_psa10_avg else "-"
    
    print(f"│ {raw_price:^27} │ {psa9_price:^27} │ {psa10_price:^23} │")
    
    # Count row
    raw_count = f"({bin_raw_count} listings)" if bin_raw_count else ""
    psa9_count = f"({bin_psa9_count} listings)" if bin_psa9_count else ""
    psa10_count = f"({bin_psa10_count} listings)" if bin_psa10_count else ""
    
    print(f"│ {raw_count:^27} │ {psa9_count:^27} │ {psa10_count:^23} │")
    
    # Link row
    print(f"│ {'[View on eBay →]':^27} │ {'[View on eBay →]':^27} │ {'[View on eBay →]':^23} │")
    print("└─────────────────────────────┴─────────────────────────────┴─────────────────────────┘")
    
    # Auction Section
    print("\n┌─────────────────────────────────────────────────────────────────────────────────────┐")
    print("│                                 AUCTIONS                                            │")
    print("├─────────────────────────────┬─────────────────────────────┬─────────────────────────┤")
    print("│            Raw              │           PSA 9             │          PSA 10         │")
    print("├─────────────────────────────┼─────────────────────────────┼─────────────────────────┤")
    
    raw_auctions = f"{auction_raw_count} active" if auction_raw_count else "None"
    psa9_auctions = f"{auction_psa9_count} active" if auction_psa9_count else "None"
    psa10_auctions = f"{auction_psa10_count} active" if auction_psa10_count else "None"
    
    print(f"│ {raw_auctions:^27} │ {psa9_auctions:^27} │ {psa10_auctions:^23} │")
    print(f"│ {'[Search eBay →]':^27} │ {'[Search eBay →]':^27} │ {'[Search eBay →]':^23} │")
    print("└─────────────────────────────┴─────────────────────────────┴─────────────────────────┘")
    
    # Print URLs for reference
    print("\n" + "-"*90)
    print("CLICKABLE LINKS (for frontend implementation):")
    print("-"*90)
    
    print("\nBUY IT NOW LINKS:")
    print(f"  Raw:    {bin_raw_url}")
    print(f"  PSA 9:  {bin_psa9_url}")
    print(f"  PSA 10: {bin_psa10_url}")
    
    print("\nAUCTION LINKS:")
    print(f"  Raw:    {auction_raw_url}")
    print(f"  PSA 9:  {auction_psa9_url}")
    print(f"  PSA 10: {auction_psa10_url}")
    
    # Output as JSON for frontend use
    print("\n" + "-"*90)
    print("JSON DATA STRUCTURE (for frontend):")
    print("-"*90)
    
    import json
    data = {
        "card": {
            "name": "Caleb Williams Planetary Pursuit The Sun",
            "epid": epid,
            "year": 2024,
            "set": "Topps Cosmic Chrome"
        },
        "bin": {
            "raw": {"avg_price": bin_raw_avg, "count": bin_raw_count, "url": bin_raw_url},
            "psa_9": {"avg_price": bin_psa9_avg, "count": bin_psa9_count, "url": bin_psa9_url},
            "psa_10": {"avg_price": bin_psa10_avg, "count": bin_psa10_count, "url": bin_psa10_url},
        },
        "auctions": {
            "raw": {"count": auction_raw_count, "url": auction_raw_url},
            "psa_9": {"count": auction_psa9_count, "url": auction_psa9_url},
            "psa_10": {"count": auction_psa10_count, "url": auction_psa10_url},
        }
    }
    
    print(json.dumps(data, indent=2))
    print("\n" + "="*90)


if __name__ == "__main__":
    main()
