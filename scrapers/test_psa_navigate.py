#!/usr/bin/env python3
"""Navigate PSA to find Topps Cosmic Chrome population."""

import httpx
from bs4 import BeautifulSoup
from datetime import datetime


def fetch_page(url: str):
    """Fetch a page from PSA."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }
    with httpx.Client(timeout=30.0, headers=headers, follow_redirects=True) as client:
        response = client.get(url)
        return response.text if response.status_code == 200 else None


def find_cosmic_chrome():
    """Navigate PSA to find 2024 Topps Cosmic Chrome."""
    print("="*60)
    print("Step 1: Get 2024 Football Sets")
    print("="*60)
    
    # Start with 2024 football cards
    html = fetch_page("https://www.psacard.com/pop/football-cards/2024")
    
    if not html:
        print("Failed to fetch 2024 football page")
        return
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Find all set links
    all_links = soup.find_all('a', href=True)
    
    # Filter for Topps sets
    topps_sets = []
    for link in all_links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        if '/pop/football-cards/2024/' in href and 'topps' in text.lower():
            topps_sets.append({
                'name': text,
                'url': 'https://www.psacard.com' + href if href.startswith('/') else href
            })
    
    print(f"\nFound {len(topps_sets)} Topps sets in 2024 Football:")
    for s in topps_sets[:15]:
        cosmic_flag = " ⭐" if 'cosmic' in s['name'].lower() else ""
        print(f"  - {s['name']}{cosmic_flag}")
    
    # Find Cosmic Chrome specifically
    cosmic_sets = [s for s in topps_sets if 'cosmic' in s['name'].lower()]
    
    if cosmic_sets:
        print(f"\n{'='*60}")
        print("Step 2: Found Cosmic Chrome!")
        print("="*60)
        
        for cosmic in cosmic_sets:
            print(f"\nSet: {cosmic['name']}")
            print(f"URL: {cosmic['url']}")
            
            # Fetch the set page
            print("\nFetching set page...")
            set_html = fetch_page(cosmic['url'])
            
            if set_html:
                set_soup = BeautifulSoup(set_html, 'lxml')
                
                # Look for subsets/inserts
                subset_links = set_soup.find_all('a', href=True)
                planetary = [l for l in subset_links 
                           if 'planetary' in l.get_text().lower() or 'pursuit' in l.get_text().lower()]
                
                if planetary:
                    print(f"\nFound Planetary Pursuit links:")
                    for p in planetary[:5]:
                        print(f"  - {p.get_text(strip=True)}: {p.get('href')}")
                
                # Look for Caleb Williams
                caleb_mentions = set_html.lower().count('caleb williams')
                print(f"\nMentions of 'Caleb Williams': {caleb_mentions}")
                
                # Find any tables with population data
                tables = set_soup.find_all('table')
                print(f"Tables found: {len(tables)}")
                
                for table in tables[:2]:
                    rows = table.find_all('tr')
                    print(f"\nTable with {len(rows)} rows:")
                    
                    # Print headers
                    headers_row = table.find('thead')
                    if headers_row:
                        headers = [th.get_text(strip=True) for th in headers_row.find_all('th')]
                        print(f"Headers: {headers[:10]}")
                    
                    # Look for Caleb Williams rows
                    for row in rows:
                        row_text = row.get_text().lower()
                        if 'caleb' in row_text or 'williams' in row_text:
                            cells = [td.get_text(strip=True) for td in row.find_all('td')]
                            if cells:
                                print(f"➡️  {cells[:8]}")
                        elif 'sun' in row_text and 'planetary' in row_text:
                            cells = [td.get_text(strip=True) for td in row.find_all('td')]
                            if cells:
                                print(f"☀️  {cells[:8]}")
    else:
        print("\n⚠️  Cosmic Chrome not found in direct listing")
        print("It may be listed under a different name or not yet in PSA's system")
    
    return topps_sets


def main():
    print("="*60)
    print("PSA Navigation - Finding Cosmic Chrome Population")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    sets = find_cosmic_chrome()
    
    print("\n" + "="*60)
    print("Complete")
    print("="*60)


if __name__ == "__main__":
    main()
