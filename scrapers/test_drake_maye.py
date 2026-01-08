#!/usr/bin/env python3
"""Complete data summary for Drake Maye Rookie Kings #3."""

import base64
import httpx
import re
from datetime import datetime
from urllib.parse import quote_plus

import os

EBAY_APP_ID = os.getenv("EBAY_APP_ID", "PeterHsu-Cardmark-PRD-50ea75066-5afd39c7")
EBAY_CERT_ID = os.getenv("EBAY_CERT_ID", "PRD-0ea750660fdd-4767-48d5-8e49-97bd")
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
    title_lower = title.lower()
    if re.search(r'psa\s*10', title_lower):
        return 'PSA_10'
    if re.search(r'psa\s*9\b', title_lower):
        return 'PSA_9'
    if re.search(r'psa\s*(\d+)', title_lower):
        return 'PSA_OTHER'
    if condition_field == 'Graded':
        return 'GRADED_UNKNOWN'
    return 'RAW'


def search_listings(token, query):
    with httpx.Client(timeout=30.0) as client:
        params = {"q": query, "category_ids": "212", "limit": 100}
        response = client.get(f"{PROD_BROWSE_URL}/item_summary/search",
            headers={"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"},
            params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('itemSummaries', []), data.get('total', 0)
        return [], 0


def organize_listings(items):
    organized = {'BIN': {'RAW': [], 'PSA_9': [], 'PSA_10': []}, 'AUCTION': {'RAW': [], 'PSA_9': [], 'PSA_10': []}}
    
    for item in items:
        title = item.get('title', '')
        condition = item.get('condition', '')
        price = float(item.get('price', {}).get('value', 0))
        buying_options = item.get('buyingOptions', [])
        epid = item.get('epid', '')
        
        listing_type = 'AUCTION' if 'AUCTION' in buying_options else 'BIN'
        card_condition = detect_condition(title, condition)
        
        if card_condition in ['RAW', 'PSA_9', 'PSA_10']:
            organized[listing_type][card_condition].append({
                'price': price, 'title': title, 'epid': epid, 'item': item
            })
    
    return organized


def calc_avg(listings):
    if not listings:
        return None
    prices = [l['price'] for l in listings if l['price'] > 0]
    return round(sum(prices) / len(prices), 2) if prices else None


def main():
    # Card info
    card = {
        "name": "Drake Maye",
        "year": 2024,
        "set": "Panini Donruss Optic",
        "subset": "Rookie Kings (SSP Case Hit)",
        "card_number": "#3",
        "epid": "23084914150"
    }
    
    # We keep the query for display/fallback, but will use EPID for the main search
    query = "Drake Maye Rookie Kings 2024 Donruss Optic"
    
    print("=" * 90)
    print("                    COMPLETE CARD DATA SUMMARY (EPID MATCHED)")
    print("=" * 90)
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 90)
    
    # === CARD INFO ===
    print("\n┌─────────────────────────────────────────────────────────────────────────────────────┐")
    print("│                                  CARD DETAILS                                       │")
    print("├─────────────────────────────────────────────────────────────────────────────────────┤")
    print(f"│  Player:      {card['name']:<72}│")
    print(f"│  Year:        {card['year']:<72}│")
    print(f"│  Set:         {card['set']:<72}│")
    print(f"│  Insert:      {card['subset']:<72}│")
    print(f"│  Card #:      {card['card_number']:<72}│")
    print(f"│  eBay EPID:   {card['epid']:<72}│")
    print("└─────────────────────────────────────────────────────────────────────────────────────┘")
    
    # === LIVE MARKET DATA (from eBay) ===
    print(f"\nFetching eBay data for EPID {card['epid']}...")
    token = get_access_token()
    
    # Search using EPID directly for precision
    with httpx.Client(timeout=30.0) as client:
        params = {"epid": card['epid'], "limit": 100}
        response = client.get(f"{PROD_BROWSE_URL}/item_summary/search",
            headers={"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"},
            params=params)
        items = response.json().get('itemSummaries', []) if response.status_code == 200 else []

    print(f"Found {len(items)} listings matching EPID")
    
    organized = organize_listings(items)
    
    # Calculate stats
    bin_raw = organized['BIN']['RAW']
    bin_psa9 = organized['BIN']['PSA_9']
    bin_psa10 = organized['BIN']['PSA_10']
    auction_raw = organized['AUCTION']['RAW']
    auction_psa9 = organized['AUCTION']['PSA_9']
    auction_psa10 = organized['AUCTION']['PSA_10']

    # === GENERATE LINKS ===
    base = quote_plus(query)
    epid_param = f"&_epid={card['epid']}"
    
    links = {
        'BIN': {
            'RAW': f"https://www.ebay.com/sch/i.html?_nkw={base}{epid_param}&LH_BIN=1",
            'PSA_9': f"https://www.ebay.com/sch/i.html?_nkw={base}{epid_param}+PSA+9&LH_BIN=1",
            'PSA_10': f"https://www.ebay.com/sch/i.html?_nkw={base}{epid_param}+PSA+10&LH_BIN=1"
        },
        'SOLD': {
            'RAW': f"https://www.ebay.com/sch/i.html?_nkw={base}{epid_param}&LH_Sold=1&LH_Complete=1",
            'PSA_9': f"https://www.ebay.com/sch/i.html?_nkw={base}{epid_param}+PSA+9&LH_Sold=1&LH_Complete=1",
            'PSA_10': f"https://www.ebay.com/sch/i.html?_nkw={base}{epid_param}+PSA+10&LH_Sold=1&LH_Complete=1"
        }
    }

    # === DATA STRUCTURE FOR FRONTEND ===
    # This dictionary represents the "Cell" data the frontend will use
    market_data = {
        'bin_stats': {
            'raw': {'avg_price': calc_avg(bin_raw), 'count': len(bin_raw), 'link': links['BIN']['RAW']},
            'psa_9': {'avg_price': calc_avg(bin_psa9), 'count': len(bin_psa9), 'link': links['BIN']['PSA_9']},
            'psa_10': {'avg_price': calc_avg(bin_psa10), 'count': len(bin_psa10), 'link': links['BIN']['PSA_10']}
        },
        'sold_links': {
             'raw': links['SOLD']['RAW'],
             'psa_9': links['SOLD']['PSA_9'],
             'psa_10': links['SOLD']['PSA_10']
        }
    }

    print("\n┌─────────────────────────────────────────────────────────────────────────────────────┐")
    print("│                            LIVE MARKET DATA (Combined)                              │")
    print("├─────────────────────────────────────────────────────────────────────────────────────┤")
    print("│                                                                                     │")
    print("│  BUY IT NOW (Avg Price + Link)                                                      │")
    print("│  ┌─────────────────────────┬─────────────────────────┬─────────────────────────┐   │")
    print("│  │          Raw            │         PSA 9           │         PSA 10          │   │")
    print("│  ├─────────────────────────┼─────────────────────────┼─────────────────────────┤   │")
    
    def fmt_cell(stats):
        if stats['avg_price']:
            price = f"${stats['avg_price']:.2f}"
            return f"{price} [↗]"
        return "- [↗]"

    c1 = fmt_cell(market_data['bin_stats']['raw'])
    c2 = fmt_cell(market_data['bin_stats']['psa_9'])
    c3 = fmt_cell(market_data['bin_stats']['psa_10'])
    
    print(f"│  │ {c1:^23} │ {c2:^23} │ {c3:^23} │   │")
    print(f"│  │ {('('+str(market_data['bin_stats']['raw']['count'])+' listings)'):^23} │ {('('+str(market_data['bin_stats']['psa_9']['count'])+' listings)'):^23} │ {('('+str(market_data['bin_stats']['psa_10']['count'])+' listings)'):^23} │   │")
    print("│  └─────────────────────────┴─────────────────────────┴─────────────────────────┘   │")
    print("│                                                                                     │")
    print("└─────────────────────────────────────────────────────────────────────────────────────┘")
    
    print("\n" + "=" * 90)
    print("JSON STRUCTURE (Ready for Frontend Integration):")
    print("=" * 90)
    import json
    print(json.dumps(market_data, indent=2))
    print("=" * 90)


if __name__ == "__main__":
    main()
