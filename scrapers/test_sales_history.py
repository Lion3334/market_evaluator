#!/usr/bin/env python3
"""Fetch historical sales data using eBay Finding API (Legacy)."""

import httpx
import json
import re
from datetime import datetime

# Use the App ID from the previous script
EBAY_APP_ID = "PeterHsu-Cardmark-PRD-50ea75066-5afd39c7"
FINDING_API_URL = "https://svcs.ebay.com/services/search/FindingService/v1"

def detect_condition(title: str) -> str:
    title_lower = title.lower()
    if re.search(r'psa\s*10', title_lower):
        return 'PSA_10'
    if re.search(r'psa\s*9\b', title_lower):
        return 'PSA_9'
    return 'RAW'

def get_historical_sales(epid):
    print(f"Fetching historical sales for EPID: {epid}")
    
    headers = {
        "X-EBAY-SOA-OPERATION-NAME": "findCompletedItems",
        "X-EBAY-SOA-SECURITY-APPNAME": EBAY_APP_ID,
        "X-EBAY-SOA-RESPONSE-DATA-FORMAT": "JSON",
    }
    
    params = {
        "productId": epid,
        "productId.@type": "ReferenceID",
        "itemFilter(0).name": "SoldItemsOnly",
        "itemFilter(0).value": "true",
        "sortOrder": "EndTimeSoonest",
        "outputSelector": "SellerInfo"
    }
    
    with httpx.Client(timeout=30.0) as client:
        response = client.get(FINDING_API_URL, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            return []
            
        data = response.json()
        
        search_result = data.get('findCompletedItemsResponse', [{}])[0].get('searchResult', [{}])[0]
        count = int(search_result.get('@count', 0))
        print(f"Found {count} sold items.")
        
        items = search_result.get('item', [])
        return items

def main():
    # Drake Maye Rookie Kings Base EPID
    epid = "23084914150"
    
    sales = get_historical_sales(epid)
    
    # Organize by grade
    organized = {'RAW': [], 'PSA_9': [], 'PSA_10': []}
    
    for item in sales:
        title = item.get('title', [''])[0]
        price_str = item.get('sellingStatus', [{}])[0].get('currentPrice', [{}])[0].get('__value__', '0')
        price = float(price_str)
        date_str = item.get('listingInfo', [{}])[0].get('endTime', [''])[0]
        
        # Parse date nicely
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            date_display = date_obj.strftime("%Y-%m-%d")
        except:
            date_display = date_str
            
        condition = detect_condition(title)
        
        if condition in organized:
            organized[condition].append({
                'date': date_display,
                'price': price,
                'title': title
            })
            
    print("\n" + "="*80)
    print("HISTORICAL SALES DATA (By Grade)")
    print("="*80)
    
    for grade in ['RAW', 'PSA_9', 'PSA_10']:
        items = organized[grade]
        if not items:
            continue
            
        avg_price = sum(i['price'] for i in items) / len(items) if items else 0
        
        print(f"\n[{grade}] - {len(items)} sales - Avg: ${avg_price:.2f}")
        print("-" * 80)
        
        # Sort by date descending
        sorted_items = sorted(items, key=lambda x: x['date'], reverse=True)
        
        for item in sorted_items[:10]:
            print(f"{item['date']} | ${item['price']:>7.2f} | {item['title'][:60]}...")

if __name__ == "__main__":
    main()
