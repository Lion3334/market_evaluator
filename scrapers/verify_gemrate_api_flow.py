import httpx
import re

BASE_URL = "https://www.gemrate.com"
SEARCH_QUERY = "2024 Donruss Downtown Jayden Daniels"

def main():
    print("1. Fetching homepage to get Token...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    client = httpx.Client(headers=headers, follow_redirects=True, timeout=30.0)
    
    resp = client.get(f"{BASE_URL}/universal-search?query={SEARCH_QUERY}")
    if resp.status_code != 200:
        print(f"Failed to load search page: {resp.status_code}")
        return

    # Extract Token
    token_match = re.search(r'const cardDetailsToken = "(.*?)";', resp.text)
    if not token_match:
        print("Could not find cardDetailsToken in page source.")
        return
    
    token = token_match.group(1)
    print(f"Token found: {token[:20]}...")

    print("\n2. Searching for card via API...")
    search_url = f"{BASE_URL}/universal-search-query"
    search_payload = {"query": SEARCH_QUERY}
    
    resp = client.post(search_url, json=search_payload)
    if resp.status_code != 200:
        print(f"Search failed: {resp.status_code}")
        return

    results = resp.json()
    print(f"Found {len(results)} results.")
    
    if not results:
        print("No results found.")
        return
        
    # Pick first result
    first_hit = results[0]
    gemrate_id = first_hit.get('gemrate_id')
    desc = first_hit.get('description')
    print(f"Selected: {desc} (ID: {gemrate_id})")
    
    print("\n3. Fetching Card Details via API...")
    details_url = f"{BASE_URL}/card-details"
    details_params = {"gemrate_id": gemrate_id}
    details_headers = headers.copy()
    details_headers["X-Card-Details-Token"] = token
    
    resp = client.get(details_url, params=details_params, headers=details_headers)
    if resp.status_code != 200:
        print(f"Details fetch failed: {resp.status_code}")
        print(resp.text[:500])
        return
        
    details = resp.json()
    print("Success! Got Details.")
    print(f"Total Pop: {details.get('total_population')}")
    print(f"Keys: {list(details.keys())[:5]}")
    
    # Check if we have breakdown
    pop_data = details.get('population_data', [])
    if pop_data:
        print(f"Population Data Graders: {[p.get('grader') for p in pop_data]}")
        
if __name__ == "__main__":
    main()
