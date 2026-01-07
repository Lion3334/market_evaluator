#!/usr/bin/env python3
"""Fetch live eBay auctions for a specific card."""

import base64
import httpx
from datetime import datetime

# Production credentials
EBAY_APP_ID = "PeterHsu-Cardmark-PRD-50ea75066-5afd39c7"
EBAY_CERT_ID = "PRD-0ea750660fdd-4767-48d5-8e49-97bd"

PROD_AUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
PROD_BROWSE_URL = "https://api.ebay.com/buy/browse/v1"


def get_access_token():
    """Get OAuth access token."""
    credentials = f"{EBAY_APP_ID}:{EBAY_CERT_ID}"
    auth_header = base64.b64encode(credentials.encode()).decode()
    
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
        if response.status_code == 200:
            return response.json().get('access_token')
        return None


def search_auctions(access_token: str, query: str, epid: str = None):
    """Search for active auctions only."""
    print(f"\nSearching for AUCTIONS: {query}")
    if epid:
        print(f"Filtering by EPID: {epid}")
    
    with httpx.Client(timeout=30.0) as client:
        # Use filter to get only auctions (not Buy It Now)
        params = {
            "q": query,
            "category_ids": "212",  # Sports Trading Cards
            "limit": 50,
            "filter": "buyingOptions:{AUCTION}",  # Only auctions
            "sort": "endingSoonest"  # Show auctions ending soon first
        }
        
        # If we have EPID, we can filter more precisely
        if epid:
            params["epid"] = epid
        
        response = client.get(
            f"{PROD_BROWSE_URL}/item_summary/search",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
            },
            params=params
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            return data.get('itemSummaries', []), data.get('total', 0)
        else:
            print(f"Error: {response.text[:500]}")
            return [], 0


def search_all_listings_filter_auctions(access_token: str, query: str):
    """Search all listings and filter for auctions client-side."""
    print(f"\nSearching ALL listings, filtering for auctions: {query}")
    
    with httpx.Client(timeout=30.0) as client:
        params = {
            "q": query,
            "category_ids": "212",
            "limit": 100,
            "sort": "endingSoonest"
        }
        
        response = client.get(
            f"{PROD_BROWSE_URL}/item_summary/search",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
            },
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('itemSummaries', [])
            
            # Filter for auctions
            auctions = [
                item for item in items 
                if 'AUCTION' in item.get('buyingOptions', [])
            ]
            
            return auctions, len(auctions), data.get('total', 0)
        return [], 0, 0


def main():
    print("="*70)
    print("Live eBay Auctions - Caleb Williams Planetary Pursuit The Sun")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Get token
    print("\nAuthenticating...")
    token = get_access_token()
    if not token:
        print("Failed to get token")
        return
    print("✓ Token obtained")
    
    # Search specifically for The Sun variant
    query = "Caleb Williams Planetary Pursuit Sun 2024 Topps Cosmic"
    epid = "2350717052"  # EPID for The Sun variant
    
    # Method 1: Direct auction filter
    print("\n" + "="*70)
    print("Method 1: Direct Auction Filter")
    print("="*70)
    auctions, total = search_auctions(token, query, epid)
    
    if auctions:
        print(f"\n✓ Found {len(auctions)} active auctions (of {total} total)")
        print_auctions(auctions)
    else:
        print(f"No auctions found with direct filter. Trying broader search...")
        
        # Method 2: Search all, filter client-side
        print("\n" + "="*70)
        print("Method 2: Search All, Filter Client-Side")
        print("="*70)
        auctions, auction_count, total = search_all_listings_filter_auctions(token, query)
        
        if auctions:
            print(f"\n✓ Found {auction_count} auctions out of {total} total listings")
            print_auctions(auctions)
        else:
            print(f"No auctions found. There may be no active auctions for this specific card right now.")
            print("Most listings are likely Buy It Now.")
    
    print("\n" + "="*70)
    print("Complete")
    print("="*70)


def print_auctions(auctions):
    """Print auction details."""
    print("\nActive Auctions:")
    print("-"*70)
    
    for i, item in enumerate(auctions[:15], 1):
        title = item.get('title', 'No title')
        
        # Get current bid price
        current_bid = item.get('currentBidPrice', item.get('price', {}))
        price = current_bid.get('value', '?')
        
        # Bid count
        bids = item.get('bidCount', 0)
        
        # Time remaining
        end_date = item.get('itemEndDate', '')
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                time_left = end_dt - datetime.now(end_dt.tzinfo)
                hours_left = time_left.total_seconds() / 3600
                if hours_left < 1:
                    time_str = f"{int(time_left.total_seconds() / 60)}m left"
                elif hours_left < 24:
                    time_str = f"{hours_left:.1f}h left"
                else:
                    time_str = f"{hours_left/24:.1f}d left"
            except:
                time_str = end_date[:16]
        else:
            time_str = "Unknown"
        
        # Condition
        condition = item.get('condition', 'Unknown')
        
        # EPID
        epid = item.get('epid', 'N/A')
        
        print(f"\n{i}. {title[:65]}{'...' if len(title) > 65 else ''}")
        print(f"   💰 Current Bid: ${price} ({bids} bids)")
        print(f"   ⏱️  {time_str}")
        print(f"   📋 Condition: {condition}")
        print(f"   🔗 {item.get('itemWebUrl', 'No URL')[:50]}...")
        
        if epid != 'N/A':
            print(f"   📦 EPID: {epid}")


if __name__ == "__main__":
    main()
