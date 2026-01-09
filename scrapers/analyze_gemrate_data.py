import httpx
import re
import json

BASE_URL = "https://www.gemrate.com"
# Jayden Daniels Downtown
SEARCH_QUERY = "2024 Donruss Downtown Jayden Daniels"

def main():
    print("--- Fetching Gemrate Data Structure ---")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    client = httpx.Client(headers=headers, follow_redirects=True, timeout=30.0)
    
    # 1. Get Token
    resp = client.get(f"{BASE_URL}/universal-search?query={SEARCH_QUERY}")
    token_match = re.search(r'const cardDetailsToken = "(.*?)";', resp.text)
    if not token_match:
        print("Error: No token")
        return
    token = token_match.group(1)
    
    # 2. Search
    search_resp = client.post(
        f"{BASE_URL}/universal-search-query", 
        json={"query": SEARCH_QUERY}
    )
    first_hit = search_resp.json()[0]
    gemrate_id = first_hit.get('gemrate_id')
    print(f"\nItem: {first_hit.get('description')}")
    print(f"ID: {gemrate_id}")
    
    # 3. Get Details
    details_headers = headers.copy()
    details_headers["X-Card-Details-Token"] = token
    details_resp = client.get(
        f"{BASE_URL}/card-details", 
        params={"gemrate_id": gemrate_id}, 
        headers=details_headers
    )
    
    data = details_resp.json()
    
    # Dump keys and structure
    print("\n--- Top Level Keys ---")
    for k in data.keys():
        print(f"- {k}")

    if 'combined_totals' in data:
        print("\n--- combined_totals ---")
        print(json.dumps(data['combined_totals'], indent=2))
        
    if 'population_data' in data:
        print(f"\n--- population_data ({len(data['population_data'])} graders) ---")
        for grader in data['population_data']:
            print(f"\nGrader: {grader.get('grader')}")
            # Show keys for grader object
            print(f"  Keys: {list(grader.keys())}")
            if 'grades' in grader:
                print(f"  Grades keys: {list(grader['grades'].keys())}")
            
            # Print the first grader's full data to see the structure of grades/metrics
            if grader.get('grader') == 'psa':
                print(json.dumps(grader, indent=2)) 

    # Check for anything appearing to be price related
    print("\n--- Searching for 'price', 'sale', 'val' in entire response ---")
    data_str = json.dumps(data)
    if "price" in data_str.lower(): print("Found 'price'")
    if "sale" in data_str.lower(): print("Found 'sale'")
    if "val" in data_str.lower(): print("Found 'val'")
    
if __name__ == "__main__":
    main()
