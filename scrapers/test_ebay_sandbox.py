#!/usr/bin/env python3
"""Test eBay API with sandbox credentials."""

import os
import base64
import httpx
from datetime import datetime

# Sandbox credentials
EBAY_APP_ID = "PeterHsu-Cardmark-SBX-894e248a9-c817466e"
EBAY_CERT_ID = "SBX-94e248a9066c-ce6b-4818-b175-65be"

# eBay Sandbox URLs (different from production)
SANDBOX_AUTH_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
SANDBOX_BROWSE_URL = "https://api.sandbox.ebay.com/buy/browse/v1"


def get_access_token():
    """Get OAuth access token from eBay sandbox."""
    credentials = f"{EBAY_APP_ID}:{EBAY_CERT_ID}"
    auth_header = base64.b64encode(credentials.encode()).decode()
    
    print("Requesting OAuth token from sandbox...")
    
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            SANDBOX_AUTH_URL,
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


def search_items(access_token: str, query: str):
    """Search for items using Browse API."""
    print(f"\nSearching for: {query}")
    
    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            f"{SANDBOX_BROWSE_URL}/item_summary/search",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
            },
            params={
                "q": query,
                "category_ids": "212",  # Sports Trading Cards
                "limit": 10
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
    print("="*60)
    print("eBay Sandbox API Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Step 1: Get access token
    token = get_access_token()
    
    if not token:
        print("\n⚠️  Could not obtain access token")
        print("Note: Sandbox may have limited data or require additional setup")
        return
    
    # Step 2: Search for the card
    query = "Caleb Williams RC Planetary Pursuit The Sun 2024 Topps Chrome Cosmic"
    items = search_items(token, query)
    
    if items:
        print(f"\n{'='*60}")
        print("Results:")
        print("="*60)
        
        for i, item in enumerate(items, 1):
            print(f"\n{i}. {item.get('title', 'No title')[:80]}")
            
            price = item.get('price', {})
            print(f"   Price: {price.get('currency', 'USD')} {price.get('value', '?')}")
            
            if item.get('itemId'):
                print(f"   Item ID: {item['itemId']}")
            
            if item.get('epid'):
                print(f"   EPID: {item['epid']}")
            
            condition = item.get('condition', item.get('conditionId', 'Unknown'))
            print(f"   Condition: {condition}")
    else:
        print("\n⚠️  No items found")
        print("Note: eBay sandbox has limited test data")
        print("Production API will have real listings")
    
    print("\n" + "="*60)
    print("Test Complete")
    print("="*60)


if __name__ == "__main__":
    main()
