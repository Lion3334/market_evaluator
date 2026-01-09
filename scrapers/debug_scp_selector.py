import requests
from bs4 import BeautifulSoup
import sys
import os

BASE_URL = "https://www.sportscardspro.com/console/football-cards-2023-panini-illusions"

def debug_selector():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    url = f"{BASE_URL}?cursor=0&sort=price&encoding=utf-8"
    print(f"Fetching: {url}")
    
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.content, "html.parser")
    
    # Target table
    rows = soup.select("table#games_table tbody tr")
    print(f"Rows found: {len(rows)}")
    
    if rows:
        first_row = rows[0]
        print("\n--- First Row HTML ---")
        print(first_row.prettify())
        
        # Try finding the title
        print("\n--- Selector Tests ---")
        
        # Test 1: td.title a (Original/Subagent suggestion)
        s1 = first_row.select_one("td.title a")
        print(f"td.title a: {s1.text.strip() if s1 else 'None'}")
        
        # Test 2: td.game-name a (Common alternative)
        s2 = first_row.select_one("td.game-name a")
        print(f"td.game-name a: {s2.text.strip() if s2 else 'None'}")
        
        # Test 3: Just 'a' (What I used, which failed/was empty?)
        s3 = first_row.select_one("a")
        print(f"a: '{s3.text.strip()}' (Attr: {s3.attrs})")

if __name__ == "__main__":
    debug_selector()
