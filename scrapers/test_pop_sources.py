#!/usr/bin/env python3
"""Try Gemrate.com for population data - often easier to scrape than PSA directly."""

import httpx
from bs4 import BeautifulSoup
from datetime import datetime


def search_gemrate(query: str):
    """Search Gemrate.com for card population."""
    print(f"Searching Gemrate for: {query}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }
    
    with httpx.Client(timeout=30.0, headers=headers, follow_redirects=True) as client:
        # Try Gemrate search
        search_url = f"https://www.gemrate.com/search"
        response = client.get(search_url, params={"q": query})
        
        print(f"Response Status: {response.status_code}")
        print(f"Final URL: {response.url}")
        
        if response.status_code == 200:
            return response.text, str(response.url)
        return None, None


def try_direct_gemrate_url():
    """Try constructing a direct Gemrate URL."""
    print("\n" + "="*60)
    print("Trying Direct Gemrate URLs")
    print("="*60)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }
    
    # Common URL patterns for Gemrate
    urls_to_try = [
        "https://www.gemrate.com/",
        "https://gemrate.com/",
    ]
    
    with httpx.Client(timeout=30.0, headers=headers, follow_redirects=True) as client:
        for url in urls_to_try:
            print(f"\nTrying: {url}")
            try:
                response = client.get(url)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'lxml')
                    title = soup.find('title')
                    print(f"Title: {title.get_text() if title else 'No title'}")
                    
                    # Look for search functionality
                    forms = soup.find_all('form')
                    inputs = soup.find_all('input')
                    print(f"Forms: {len(forms)}, Input fields: {len(inputs)}")
                    
                    # Check for any card-related content
                    card_mentions = response.text.lower().count('card')
                    psa_mentions = response.text.lower().count('psa')
                    print(f"Mentions - 'card': {card_mentions}, 'psa': {psa_mentions}")
                    
                    return response.text
                    
            except Exception as e:
                print(f"Error: {e}")
    
    return None


def try_psa_pop_api():
    """Check if PSA has any API endpoints we can use."""
    print("\n" + "="*60)
    print("Checking for PSA Data Endpoints")
    print("="*60)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json, text/html",
    }
    
    with httpx.Client(timeout=30.0, headers=headers, follow_redirects=True) as client:
        # Try PSA pop search with specific query
        search_url = "https://www.psacard.com/pop"
        params = {"q": "topps cosmic chrome 2024"}
        
        print(f"Searching: {search_url}")
        response = client.get(search_url, params=params)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Check page structure
            title = soup.find('title')
            print(f"Page title: {title.get_text() if title else 'No title'}")
            
            # Look for any data in script tags (often where JS frameworks store data)
            scripts = soup.find_all('script')
            for script in scripts:
                script_text = script.get_text()
                if 'cosmic' in script_text.lower() or 'topps' in script_text.lower():
                    print(f"\nFound relevant script content ({len(script_text)} chars)")
                    # Print first bit
                    if len(script_text) > 100:
                        print(f"Preview: {script_text[:200]}...")
            
            # Look for any JSON data embedded in the page
            import re
            json_pattern = r'\{[^{}]*"pop"[^{}]*\}'
            matches = re.findall(json_pattern, response.text[:50000])  # Limit search
            if matches:
                print(f"\nFound {len(matches)} potential JSON objects with 'pop' data")


def main():
    print("="*60)
    print("Alternative Population Data Sources")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print("\nTarget: Caleb Williams - Planetary Pursuit 'The Sun'")
    print("="*60)
    
    # Try Gemrate
    html, url = search_gemrate("Caleb Williams Planetary Pursuit Sun")
    if html:
        print(f"Got Gemrate response: {len(html)} bytes")
        soup = BeautifulSoup(html, 'lxml')
        title = soup.find('title')
        print(f"Title: {title.get_text() if title else 'Unknown'}")
    
    # Try direct Gemrate
    try_direct_gemrate_url()
    
    # Check PSA for API/data
    try_psa_pop_api()
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print("""
Finding: PSA website is heavily JavaScript-based.
Population data is loaded dynamically, not in initial HTML.

Options for getting PSA data:
1. Use a browser automation tool (Playwright/Puppeteer) to render JS
2. Find and use PSA's internal API endpoints
3. Use a data aggregator that already scrapes PSA (like Gemrate)
4. Manual data entry for initial cards, then automate later

For MVP, we could:
- Focus on eBay data first (working!)
- Manually input population for test cards
- Add PSA scraping with browser automation later
""")
    print("="*60)


if __name__ == "__main__":
    main()
