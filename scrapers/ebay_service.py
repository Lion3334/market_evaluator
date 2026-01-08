import os
import base64
import httpx
import time

class EbayService:
    PROD_AUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
    PROD_BROWSE_URL = "https://api.ebay.com/buy/browse/v1"

    def __init__(self, app_id, cert_id):
        self.app_id = app_id
        self.cert_id = cert_id
        self.token = None
        self.token_expiry = 0

    def get_token(self):
        if self.token and time.time() < self.token_expiry:
            return self.token

        credentials = f"{self.app_id}:{self.cert_id}"
        auth_header = base64.b64encode(credentials.encode()).decode()
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.PROD_AUTH_URL,
                    headers={
                        "Authorization": f"Basic {auth_header}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={
                        "grant_type": "client_credentials",
                        "scope": "https://api.ebay.com/oauth/api_scope"
                    }
                )
                response.raise_for_status()
                data = response.json()
                self.token = data['access_token']
                # Expire 60s before actual expiry to be safe
                self.token_expiry = time.time() + data['expires_in'] - 60
                return self.token
        except Exception as e:
            print(f"Error getting token: {e}")
            return None

    def search_item(self, query, limit=10):
        token = self.get_token()
        if not token:
            return []

        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }
        params = {"q": query, "limit": limit}

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.PROD_BROWSE_URL}/item_summary/search",
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                return response.json().get('itemSummaries', [])
        except Exception as e:
            print(f"Error searching items: {e}")
            return []

    def find_best_epid(self, query):
        items = self.search_item(query, limit=50)
        epid_counts = {}
        epid_titles = {}

        for item in items:
            epid = item.get('epid')
            if epid:
                epid_counts[epid] = epid_counts.get(epid, 0) + 1
                epid_titles[epid] = item.get('title')

        if not epid_counts:
            return None, None

        # Return most frequent EPID
        best_epid = max(epid_counts, key=epid_counts.get)
        return best_epid, epid_titles[best_epid]

    def get_sold_listings(self, epid, limit=200):
        """
        Fetch sold listings for a specific EPID.
        Note: The Browse API 'search' endpoint supports filtering by EPID.
        To get SOLD items, we need to use the specific filter logic or 'item_summary/search' with specific compatibility checking?
        Actually, Browse API allows searching for completed items using `filter=buyingOptions:{FIXED_PRICE|AUCTION}` and other params?
        Wait, standard Browse API doesn't easily show SOLD items unless you use `filter` param.
        Let's try: `filter=price:[..],priceCurrency:USD` etc.
        For SOLD items, we typically need the 'Finding API' (older) or check specific Browse filters.
        Actually, looking at `find_epid.py`, it was just searching active listings.
        
        Correct way to find SOLD items via Browse API is unfortunately tricky or requires Marketplace Insights API (Restricted).
        However, searching with `epid` and checking "completed" is not directly supported in Browse v1 public search easily without finding API.
        But let's try to mimic `buyingOptions` or check if we can filter by `deliveryCountry` etc.
        
        Actually, for this MVP, if we can't reliably get SOLD data via Browse API for *historical* checks (Finding API is deprecated but often serves this), 
        we might have to rely on the scraping or `item` endpoint if we have specific item IDs.
        
        BUT, we can try to filter `item_summary/search`? 
        No, `item_summary/search` finds AVAILABLE items.
        
        Alternative: finding_advanced (Finding API) is the standard for sold.
        Let's assume we use Finding API logic if wrapping `ebay-sdk` or constructing raw XML/SOAP/GET requests.
        Or, we can check if the user has Finding API access. 
        Using `findItemsAdvanced` with `outputSelector=SellingStatus` and `itemFilter.name=SoldItemsOnly`.
        
        Since I am writing raw requests, maybe I stick to Browse API for *identifying* the card, 
        but for *sales history*, I might have to use Finding API encoded in URL params if enabled.
        
        Let's assume for this MVP step we try the Finding API URL construction.
        """
        # ... logic to be implemented in fetch_sales.py leveraging strict EPID ...
        pass
