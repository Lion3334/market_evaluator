import httpx
from ebay_service import EbayService

import os

APP_ID = os.getenv("EBAY_APP_ID")
CERT_ID = os.getenv("EBAY_CERT_ID")
FINDING_URL = "https://svcs.ebay.com/services/search/FindingService/v1"

def test_api():
    service = EbayService(APP_ID, CERT_ID)
    token = service.get_token()
    print(f"Token: {token[:10]}...")
    
    headers = {
        "X-EBAY-SOA-OPERATION-NAME": "findCompletedItems",
        "X-EBAY-SOA-SECURITY-APPNAME": APP_ID,
        "X-EBAY-SOA-SERVICE-VERSION": "1.13.0",
        "X-EBAY-SOA-RESPONSE-DATA-FORMAT": "JSON",
        "X-EBAY-SOA-GLOBAL-ID": "EBAY-US",
        "X-EBAY-API-IAF-TOKEN": token
    }
    
    params = {
        "keywords": "Harry Potter",
        "itemFilter(0).name": "SoldItemsOnly",
        "itemFilter(0).value": "true",
        "paginationInput.entriesPerPage": "1"
    }
    
    resp = httpx.get(FINDING_URL, headers=headers, params=params)
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text[:500]}")

if __name__ == "__main__":
    test_api()
