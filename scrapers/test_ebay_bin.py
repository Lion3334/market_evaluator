#!/usr/bin/env python3
"""Fetch Buy It Now listings for the Caleb Williams The Sun card."""

import base64
import httpx
from datetime import datetime
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

def search_bin_listings(token, query, epid=None):
    """Search for Buy It Now listings only."""
    with httpx.Client(timeout=30.0) as client:
        params = {
            "q": query,
            "category_ids": "212",
            "limit": 50,
            "filter": "buyingOptions:{FIXED_PRICE}",
            "sort": "price"
        }
        if epid:
            params["epid"] = epid
        
        response = client.get(f"{PROD_BROWSE_URL}/item_summary/search",
            headers={"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"},
            params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('itemSummaries', []), data.get('total', 0)
        return [], 0

print("="*70)
print("Buy It Now Listings - Caleb Williams Planetary Pursuit The Sun")
print("="*70)

token = get_access_token()
query = "Caleb Williams Planetary Pursuit Sun 2024 Topps Cosmic"
epid = "2350717052"

items, total = search_bin_listings(token, query, epid)
print(f"\n✓ Found {total} Buy It Now listings\n")

for i, item in enumerate(items[:20], 1):
    title = item.get('title', '')[:60]
    price = item.get('price', {}).get('value', '?')
    condition = item.get('condition', 'Unknown')
    epid_val = item.get('epid', 'N/A')
    
    print(f"{i:2}. ${price:>7} | {condition:12} | {title}...")
    
print(f"\n{'='*70}")
