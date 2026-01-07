"""eBay API client for fetching sales and listings data.

Uses eBay Browse API for completed items and Finding API for search.
Requires eBay Developer credentials in .env file.
"""

import os
import base64
import httpx
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv(dotenv_path='../../.env')


@dataclass
class EbaySale:
    """Represents a completed eBay sale."""
    item_id: str
    title: str
    price: float
    currency: str
    sale_date: datetime
    condition: str
    seller_id: str
    image_url: Optional[str] = None
    epid: Optional[str] = None


@dataclass
class EbayListing:
    """Represents an active eBay listing."""
    item_id: str
    title: str
    price: float
    currency: str
    listing_type: str  # AUCTION, FIXED_PRICE
    buy_now_price: Optional[float]
    bid_count: int
    end_time: Optional[datetime]
    condition: str
    seller_id: str
    seller_rating: float
    image_urls: list[str]
    item_url: str
    shipping_cost: Optional[float] = None
    epid: Optional[str] = None


class EbayClient:
    """Client for eBay Browse and Finding APIs."""
    
    BROWSE_API_BASE = "https://api.ebay.com/buy/browse/v1"
    AUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
    
    def __init__(self):
        self.app_id = os.getenv('EBAY_APP_ID')
        self.cert_id = os.getenv('EBAY_CERT_ID')
        self.oauth_token = os.getenv('EBAY_OAUTH_TOKEN')
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self.client = httpx.Client(timeout=30.0)
    
    def _get_auth_header(self) -> str:
        """Get base64 encoded auth header for OAuth."""
        credentials = f"{self.app_id}:{self.cert_id}"
        return base64.b64encode(credentials.encode()).decode()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _refresh_access_token(self) -> str:
        """Get or refresh OAuth access token."""
        response = self.client.post(
            self.AUTH_URL,
            headers={
                "Authorization": f"Basic {self._get_auth_header()}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope"
            }
        )
        response.raise_for_status()
        data = response.json()
        self._access_token = data['access_token']
        return self._access_token
    
    def _get_headers(self) -> dict:
        """Get headers for API requests."""
        if not self._access_token:
            self._refresh_access_token()
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def search_items(
        self, 
        query: str, 
        category_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort: str = "endingSoonest"
    ) -> list[EbayListing]:
        """Search for active listings."""
        params = {
            "q": query,
            "limit": limit,
            "offset": offset,
            "sort": sort
        }
        if category_id:
            params["category_ids"] = category_id
        
        response = self.client.get(
            f"{self.BROWSE_API_BASE}/item_summary/search",
            headers=self._get_headers(),
            params=params
        )
        response.raise_for_status()
        data = response.json()
        
        listings = []
        for item in data.get('itemSummaries', []):
            listing = self._parse_listing(item)
            if listing:
                listings.append(listing)
        
        return listings
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def get_item(self, item_id: str) -> Optional[EbayListing]:
        """Get details for a specific item."""
        response = self.client.get(
            f"{self.BROWSE_API_BASE}/item/{item_id}",
            headers=self._get_headers()
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return self._parse_listing(response.json())
    
    def _parse_listing(self, item: dict) -> Optional[EbayListing]:
        """Parse an item from API response into EbayListing."""
        try:
            price_info = item.get('price', {})
            current_bid = item.get('currentBidPrice', {})
            
            # Determine listing type
            buying_options = item.get('buyingOptions', [])
            if 'AUCTION' in buying_options:
                listing_type = 'AUCTION'
                price = float(current_bid.get('value', 0)) or float(price_info.get('value', 0))
            else:
                listing_type = 'FIXED_PRICE'
                price = float(price_info.get('value', 0))
            
            # Parse end time
            end_time = None
            if item.get('itemEndDate'):
                end_time = datetime.fromisoformat(item['itemEndDate'].replace('Z', '+00:00'))
            
            # Get images
            image_urls = []
            if item.get('image'):
                image_urls.append(item['image'].get('imageUrl', ''))
            if item.get('additionalImages'):
                for img in item['additionalImages']:
                    image_urls.append(img.get('imageUrl', ''))
            
            # Seller info
            seller = item.get('seller', {})
            
            return EbayListing(
                item_id=item.get('itemId', item.get('legacyItemId', '')),
                title=item.get('title', ''),
                price=price,
                currency=price_info.get('currency', 'USD'),
                listing_type=listing_type,
                buy_now_price=float(price_info.get('value', 0)) if 'FIXED_PRICE' in buying_options else None,
                bid_count=item.get('bidCount', 0),
                end_time=end_time,
                condition=item.get('condition', 'Unknown'),
                seller_id=seller.get('username', ''),
                seller_rating=float(seller.get('feedbackPercentage', 0)),
                image_urls=image_urls,
                item_url=item.get('itemWebUrl', ''),
                shipping_cost=self._parse_shipping(item),
                epid=item.get('epid')
            )
        except Exception as e:
            print(f"Error parsing listing: {e}")
            return None
    
    def _parse_shipping(self, item: dict) -> Optional[float]:
        """Parse shipping cost from item."""
        shipping_options = item.get('shippingOptions', [])
        if shipping_options:
            cost = shipping_options[0].get('shippingCost', {}).get('value')
            return float(cost) if cost else None
        return None


# Trading card categories on eBay
EBAY_CATEGORIES = {
    'sports_trading_cards': '212',
    'pokemon_cards': '183454',
    'magic_cards': '19107',
    'yugioh_cards': '2536',
}
