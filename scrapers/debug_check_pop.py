import httpx
from bs4 import BeautifulSoup

URL = "https://www.sportscardspro.com/game/football-cards-2024-panini-donruss-downtown/jayden-daniels-d-jd"

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    print(f"Fetching {URL}...")
    resp = httpx.get(URL, headers=headers, follow_redirects=True)
    
    if resp.status_code != 200:
        print(f"Failed: {resp.status_code}")
        return

    soup = BeautifulSoup(resp.text, "lxml")
    
    # 1. Search for keywords
    keywords = ["population", "pop report", "graded count", "census", "psa 10", "gem mint", "gem rate"]
    
    print("\n--- Keyword Search ---")
    text_content = soup.get_text().lower()
    for kw in keywords:
        count = text_content.count(kw)
        print(f"'{kw}': found {count} times")
        
    # 2. Look for tables that might contain this info
    print("\n--- Table Headers ---")
    tables = soup.find_all("table")
    for i, table in enumerate(tables):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        print(f"Table {i}: {headers}")
        
    # 3. Look for 'PSA 10' related context
    print("\n--- Context around 'PSA 10' ---")
    # specific elements containing 'PSA 10'
    elements = soup.find_all(string=lambda text: text and "PSA 10" in text)
    for i, el in enumerate(elements[:5]): # First 5
        parent = el.parent
        print(f"Match {i}: {parent.name} -> {el.strip()}")
        print(f"  Parent Class: {parent.get('class')}")
        
if __name__ == "__main__":
    main()
