#!/usr/bin/env python3
"""Complete data summary for Caleb Williams Planetary Pursuit The Sun."""

import base64
import httpx
import re
import json
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


def search_listings(token, query, epid=None):
    with httpx.Client(timeout=30.0) as client:
        params = {"q": query, "category_ids": "212", "limit": 100}
        if epid:
            params["epid"] = epid
        response = client.get(f"{PROD_BROWSE_URL}/item_summary/search",
            headers={"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"},
            params=params)
        return response.json().get('itemSummaries', []) if response.status_code == 200 else []


def organize_listings(items):
    organized = {'BIN': {'RAW': [], 'PSA_9': [], 'PSA_10': []}, 'AUCTION': {'RAW': [], 'PSA_9': [], 'PSA_10': []}}
    
    for item in items:
        title = item.get('title', '')
        condition = item.get('condition', '')
        price = float(item.get('price', {}).get('value', 0))
        buying_options = item.get('buyingOptions', [])
        
        listing_type = 'AUCTION' if 'AUCTION' in buying_options else 'BIN'
        card_condition = detect_condition(title, condition)
        
        if card_condition in ['RAW', 'PSA_9', 'PSA_10']:
            organized[listing_type][card_condition].append({'price': price, 'title': title})
    
    return organized


def calc_avg(listings):
    if not listings:
        return None
    prices = [l['price'] for l in listings if l['price'] > 0]
    return round(sum(prices) / len(prices), 2) if prices else None


def main():
    # Card info
    card = {
        "name": "Caleb Williams",
        "year": 2024,
        "set": "Topps Cosmic Chrome",
        "subset": "Planetary Pursuit",
        "parallel": "The Sun",
        "card_number": "CW",
        "epid": "2350717052"
    }
    
    query = "Caleb Williams Planetary Pursuit Sun 2024 Topps Cosmic"
    
    print("=" * 90)
    print("                    COMPLETE CARD DATA SUMMARY")
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
    print(f"│  Parallel:    {card['parallel']:<72}│")
    print(f"│  Card #:      {card['card_number']:<72}│")
    print(f"│  eBay EPID:   {card['epid']:<72}│")
    print("└─────────────────────────────────────────────────────────────────────────────────────┘")
    
    # === GRADING DATA (from Gemrate) ===
    # Hardcoded from our earlier Gemrate scrape
    grading_data = {
        "total_pop": 136,
        "gem_rate": 60.3,
        "psa": {"total": 129, "10": 79, "9": 37, "8": 9, "7": 3, "gem_rate": 61.2},
        "sgc": {"total": 7, "10": 3, "9.5": 3, "9": 1}
    }
    
    print("\n┌─────────────────────────────────────────────────────────────────────────────────────┐")
    print("│                              GRADING DATA (Gemrate)                                 │")
    print("├─────────────────────────────────────────────────────────────────────────────────────┤")
    print(f"│  Total Population:     {grading_data['total_pop']:<64}│")
    print(f"│  Universal Gem Rate:   {grading_data['gem_rate']}%{' '*61}│")
    print("├─────────────────────────────────────────────────────────────────────────────────────┤")
    print("│  PSA Breakdown:                                                                     │")
    print(f"│    Total Graded:  {grading_data['psa']['total']:<69}│")
    print(f"│    PSA 10 (Gem):  {grading_data['psa']['10']:<69}│")
    print(f"│    PSA 9 (Mint):  {grading_data['psa']['9']:<69}│")
    print(f"│    PSA 8:         {grading_data['psa']['8']:<69}│")
    print(f"│    PSA 7:         {grading_data['psa']['7']:<69}│")
    print(f"│    PSA Gem Rate:  {grading_data['psa']['gem_rate']}%{' '*64}│")
    print("├─────────────────────────────────────────────────────────────────────────────────────┤")
    print("│  SGC Breakdown:                                                                     │")
    print(f"│    Total Graded:  {grading_data['sgc']['total']:<69}│")
    print(f"│    SGC 10:        {grading_data['sgc']['10']:<69}│")
    print(f"│    SGC 9.5:       {grading_data['sgc']['9.5']:<69}│")
    print(f"│    SGC 9:         {grading_data['sgc']['9']:<69}│")
    print("└─────────────────────────────────────────────────────────────────────────────────────┘")
    
    # === LIVE MARKET DATA (from eBay) ===
    token = get_access_token()
    items = search_listings(token, query, card['epid'])
    organized = organize_listings(items)
    
    # Calculate stats
    bin_raw = organized['BIN']['RAW']
    bin_psa9 = organized['BIN']['PSA_9']
    bin_psa10 = organized['BIN']['PSA_10']
    auction_raw = organized['AUCTION']['RAW']
    auction_psa9 = organized['AUCTION']['PSA_9']
    auction_psa10 = organized['AUCTION']['PSA_10']
    
    print("\n┌─────────────────────────────────────────────────────────────────────────────────────┐")
    print("│                            LIVE MARKET DATA (eBay)                                  │")
    print("├─────────────────────────────────────────────────────────────────────────────────────┤")
    print("│                                                                                     │")
    print("│  BUY IT NOW - Average Prices                                                        │")
    print("│  ┌─────────────────────────┬─────────────────────────┬─────────────────────────┐   │")
    print("│  │          Raw            │         PSA 9           │         PSA 10          │   │")
    print("│  ├─────────────────────────┼─────────────────────────┼─────────────────────────┤   │")
    
    raw_price = f"${calc_avg(bin_raw):.2f}" if calc_avg(bin_raw) else "-"
    psa9_price = f"${calc_avg(bin_psa9):.2f}" if calc_avg(bin_psa9) else "-"
    psa10_price = f"${calc_avg(bin_psa10):.2f}" if calc_avg(bin_psa10) else "-"
    
    print(f"│  │ {raw_price:^23} │ {psa9_price:^23} │ {psa10_price:^23} │   │")
    print(f"│  │ {'(' + str(len(bin_raw)) + ' listings)':^23} │ {'(' + str(len(bin_psa9)) + ' listings)':^23} │ {'(' + str(len(bin_psa10)) + ' listings)':^23} │   │")
    print("│  │      [View on eBay]     │      [View on eBay]     │      [View on eBay]     │   │")
    print("│  └─────────────────────────┴─────────────────────────┴─────────────────────────┘   │")
    print("│                                                                                     │")
    print("│  AUCTIONS - Active Count                                                            │")
    print("│  ┌─────────────────────────┬─────────────────────────┬─────────────────────────┐   │")
    print("│  │          Raw            │         PSA 9           │         PSA 10          │   │")
    print("│  ├─────────────────────────┼─────────────────────────┼─────────────────────────┤   │")
    
    raw_auctions = f"{len(auction_raw)} active" if auction_raw else "None"
    psa9_auctions = f"{len(auction_psa9)} active" if auction_psa9 else "None"
    psa10_auctions = f"{len(auction_psa10)} active" if auction_psa10 else "None"
    
    print(f"│  │ {raw_auctions:^23} │ {psa9_auctions:^23} │ {psa10_auctions:^23} │   │")
    print("│  │     [Search eBay]       │     [Search eBay]       │     [Search eBay]       │   │")
    print("│  └─────────────────────────┴─────────────────────────┴─────────────────────────┘   │")
    print("│                                                                                     │")
    print("└─────────────────────────────────────────────────────────────────────────────────────┘")
    
    # === EBAY LINKS ===
    print("\n┌─────────────────────────────────────────────────────────────────────────────────────┐")
    print("│                                 EBAY LINKS                                          │")
    print("├─────────────────────────────────────────────────────────────────────────────────────┤")
    
    base = quote_plus(query)
    print(f"│  BIN Raw:     https://www.ebay.com/sch/i.html?_nkw={base}&LH_BIN=1")
    print(f"│  BIN PSA 9:   https://www.ebay.com/sch/i.html?_nkw={base}+PSA+9&LH_BIN=1")
    print(f"│  BIN PSA 10:  https://www.ebay.com/sch/i.html?_nkw={base}+PSA+10&LH_BIN=1")
    print("│                                                                                     │")
    print(f"│  Auction Raw:    https://www.ebay.com/sch/i.html?_nkw={base}&LH_Auction=1")
    print(f"│  Auction PSA 9:  https://www.ebay.com/sch/i.html?_nkw={base}+PSA+9&LH_Auction=1")
    print(f"│  Auction PSA 10: https://www.ebay.com/sch/i.html?_nkw={base}+PSA+10&LH_Auction=1")
    print("└─────────────────────────────────────────────────────────────────────────────────────┘")
    
    print("\n" + "=" * 90)
    print("                              END OF SUMMARY")
    print("=" * 90)


if __name__ == "__main__":
    main()
