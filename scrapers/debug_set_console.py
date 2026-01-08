import httpx
from bs4 import BeautifulSoup

URL = "https://www.sportscardspro.com/console/football-cards-2024-panini-donruss-downtown"

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    print(f"Fetching {URL}...")
    resp = httpx.get(URL, headers=headers, follow_redirects=True)
    
    soup = BeautifulSoup(resp.text, "lxml")
    
    tables = soup.find_all("table")
    print(f"Found {len(tables)} tables.")
    
    for i, table in enumerate(tables):
        print(f"\n--- Table {i} ---")
        headers = [th.text.strip() for th in table.find_all("th")]
        print(f"Headers: {headers}")
        
        rows = table.find_all("tr")
        print(f"Row count: {len(rows)}")
        if len(rows) > 0:
            first_row_cols = [td.text.strip().replace('\n', ' ') for td in rows[1].find_all("td")]
            print(f"First data row: {first_row_cols}")
            
if __name__ == "__main__":
    main()
