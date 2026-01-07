#!/usr/bin/env python3
"""Test PSA Population scraping for a specific card."""

import re
import time
import httpx
from datetime import datetime
from bs4 import BeautifulSoup


def search_psa_pop(query: str):
    """Search PSA pop report for a set/card."""
    print(f"Searching PSA for: {query}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    with httpx.Client(timeout=30.0, headers=headers, follow_redirects=True) as client:
        # Try the PSA pop search
        search_url = "https://www.psacard.com/pop"
        response = client.get(search_url, params={"q": query})
        
        print(f"Search Response Status: {response.status_code}")
        
        if response.status_code == 200:
            return response.text
        else:
            print(f"Search failed: {response.status_code}")
            return None


def search_psa_cert_verification(cert_number: str = None):
    """Try PSA cert verification lookup."""
    print("\nTrying PSA Cert Verification...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    # PSA's public verification page
    with httpx.Client(timeout=30.0, headers=headers, follow_redirects=True) as client:
        # Try to access the population report main page
        pop_url = "https://www.psacard.com/pop/football-cards/2024/topps-cosmic-chrome/183657"
        print(f"Trying: {pop_url}")
        
        response = client.get(pop_url)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            return response.text
        return None


def parse_pop_results(html: str, search_term: str = "Caleb Williams"):
    """Parse PSA pop report HTML for card data."""
    soup = BeautifulSoup(html, 'lxml')
    
    # Look for search results or card tables
    results = []
    
    # Try to find set links
    set_links = soup.select('a[href*="/pop/"]')
    print(f"\nFound {len(set_links)} pop links")
    
    for link in set_links[:20]:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        if 'cosmic' in text.lower() or 'topps' in text.lower() or '2024' in text.lower():
            print(f"  - {text}: {href}")
            results.append({'name': text, 'url': href})
    
    # Try to find any tables with population data
    tables = soup.select('table')
    print(f"\nFound {len(tables)} tables")
    
    for i, table in enumerate(tables[:3]):
        rows = table.select('tr')
        print(f"\nTable {i+1}: {len(rows)} rows")
        for row in rows[:5]:
            cells = row.select('td, th')
            if cells:
                cell_text = [c.get_text(strip=True)[:30] for c in cells[:6]]
                if any(search_term.lower() in ' '.join(cell_text).lower() for _ in [1]):
                    print(f"  → {cell_text}")
    
    return results


def try_direct_set_lookup():
    """Try direct lookup of known PSA set URLs."""
    print("\n" + "="*60)
    print("Trying Direct PSA Set Lookup")
    print("="*60)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }
    
    # Known PSA pop report URL patterns for 2024 Topps
    # Format: /pop/{sport}-cards/{year}/{set-name}/{set-id}
    potential_urls = [
        "https://www.psacard.com/pop/football-cards/2024",
        "https://www.psacard.com/pop/search?query=topps+cosmic+chrome+2024",
    ]
    
    with httpx.Client(timeout=30.0, headers=headers, follow_redirects=True) as client:
        for url in potential_urls:
            print(f"\nTrying: {url}")
            try:
                response = client.get(url)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'lxml')
                    
                    # Look for cosmic chrome
                    links = soup.find_all('a', href=True)
                    cosmic_links = [l for l in links if 'cosmic' in l.get_text().lower()]
                    
                    if cosmic_links:
                        print(f"Found {len(cosmic_links)} Cosmic Chrome links:")
                        for link in cosmic_links[:5]:
                            print(f"  - {link.get_text(strip=True)}: {link.get('href')}")
                    else:
                        # Look for any 2024 Topps sets
                        topps_links = [l for l in links if 'topps' in l.get_text().lower() and '2024' in l.get_text().lower()]
                        if topps_links:
                            print(f"Found {len(topps_links)} 2024 Topps links:")
                            for link in topps_links[:10]:
                                print(f"  - {link.get_text(strip=True)}")
                                
            except Exception as e:
                print(f"Error: {e}")


def main():
    print("="*60)
    print("PSA Population Scraper Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print("\nTarget: 2024 Topps Chrome Cosmic Planetary Pursuit")
    print("        Caleb Williams - 'The Sun' variant")
    print("="*60)
    
    # Step 1: Try PSA pop search
    query = "2024 Topps Cosmic Chrome Football"
    html = search_psa_pop(query)
    
    if html:
        print(f"\n✓ Got response ({len(html)} bytes)")
        results = parse_pop_results(html, "Caleb Williams")
    
    # Step 2: Try direct set lookup
    try_direct_set_lookup()
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print("""
PSA scraping requires:
1. Finding the correct set URL in PSA's system
2. Navigating to the specific card within that set
3. Extracting population counts per grade

PSA's website structure may require:
- Browsing by year → manufacturer → set → subset
- Or searching and following result links

For 'The Sun' variant, we need to find:
- Set: 2024 Topps Cosmic Chrome (or similar)
- Insert: Planetary Pursuit
- Card: Caleb Williams
- Variant: The Sun
""")
    print("="*60)


if __name__ == "__main__":
    main()
