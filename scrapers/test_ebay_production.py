#!/usr/bin/env python3
"""Test eBay Production API with credentials."""

import os
import base64
import httpx
from datetime import datetime

# Production credentials
# Production credentials
EBAY_APP_ID = os.getenv("EBAY_APP_ID")
EBAY_CERT_ID = os.getenv("EBAY_CERT_ID")

# eBay Production URLs
PROD_AUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
PROD_BROWSE_URL = "https://api.ebay.com/buy/browse/v1"


def get_access_token():
    """Get OAuth access token from eBay production."""
    credentials = f"{EBAY_APP_ID}:{EBAY_CERT_ID}"
    auth_header = base64.b64encode(credentials.encode()).decode()
    
    print("Requesting OAuth token from production...")
    
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            PROD_AUTH_URL,
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope"
            }
        )
        
        print(f"Auth Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Token obtained, expires in {data.get('expires_in', 'unknown')} seconds")
            return data.get('access_token')
        else:
            print(f"✗ Auth failed: {response.text}")
            return None


def search_items(access_token: str, query: str, limit: int = 10):
    """Search for items using Browse API."""
    print(f"\nSearching for: {query}")
    
    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            f"{PROD_BROWSE_URL}/item_summary/search",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
            },
            params={
                "q": query,
                "category_ids": "212",  # Sports Trading Cards
                "limit": limit
            }
        )
        
        print(f"Search Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('itemSummaries', [])
            total = data.get('total', 0)
            print(f"✓ Found {total} total items, showing {len(items)}")
            return items
        else:
            print(f"✗ Search failed: {response.text[:500]}")
            return []


def main():
    print("="*70)
    print("eBay PRODUCTION API Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Step 1: Get access token
    token = get_access_token()
    
    if not token:
        print("\n⚠️  Could not obtain access token")
        return
    
    # Step 2: Search for the Caleb Williams card
    query = "Caleb Williams RC Planetary Pursuit The Sun 2024 Topps Chrome Cosmic"
    items = search_items(token, query)
    
    if items:
        print(f"\n{'='*70}")
        print("LIVE LISTINGS FOUND:")
        print("="*70)
        
        for i, item in enumerate(items, 1):
            title = item.get('title', 'No title')
            print(f"\n{i}. {title[:75]}{'...' if len(title) > 75 else ''}")
            
            # Price
            price = item.get('price', {})
            print(f"   💰 Price: ${price.get('value', '?')} {price.get('currency', 'USD')}")
            
            # Item ID and EPID
            if item.get('itemId'):
                print(f"   🔑 Item ID: {item['itemId']}")
            if item.get('epid'):
                print(f"   📦 EPID: {item['epid']}")
            
            # Condition
            condition = item.get('condition', 'Unknown')
            print(f"   📋 Condition: {condition}")
            
            # Buying options
            buying = item.get('buyingOptions', [])
            print(f"   🛒 Type: {', '.join(buying)}")
            
            # URL
            url = item.get('itemWebUrl', '')
            if url:
                print(f"   🔗 {url[:60]}...")
    else:
        print("\n⚠️  No items found for this specific query")
        print("Trying a broader search...")
        
        # Try broader search
        broader_query = "Caleb Williams 2024 Topps Chrome Cosmic"
        items = search_items(token, broader_query, limit=5)
        
        if items:
            print(f"\n{'='*70}")
            print(f"Results for broader query: '{broader_query}'")
            print("="*70)
            for i, item in enumerate(items, 1):
                title = item.get('title', 'No title')
                price = item.get('price', {})
                print(f"\n{i}. {title[:70]}...")
                print(f"   💰 ${price.get('value', '?')}")
    
    print("\n" + "="*70)
    print("Test Complete")
    print("="*70)


if __name__ == "__main__":
    main()
