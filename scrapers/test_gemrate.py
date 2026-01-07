#!/usr/bin/env python3
"""Focused Gemrate.com scraper for population data."""

import httpx
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re


def search_gemrate(query: str):
    """Search Gemrate and parse results."""
    print(f"Searching Gemrate for: {query}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    with httpx.Client(timeout=30.0, headers=headers, follow_redirects=True) as client:
        # Gemrate search URL
        response = client.get(
            "https://www.gemrate.com/universal-search",
            params={"query": query}
        )
        
        print(f"Status: {response.status_code}")
        print(f"URL: {response.url}")
        
        if response.status_code == 200:
            return parse_gemrate_search(response.text)
        return []


def parse_gemrate_search(html: str):
    """Parse Gemrate search results page."""
    soup = BeautifulSoup(html, 'lxml')
    results = []
    
    # Look for card entries in the page
    # Gemrate likely has cards in divs or table rows
    
    # Try finding any links to card detail pages
    card_links = soup.find_all('a', href=True)
    for link in card_links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        # Look for links that might be to individual cards
        if '/card/' in href or '/set/' in href or '/item/' in href:
            results.append({
                'text': text,
                'url': href if href.startswith('http') else f"https://www.gemrate.com{href}"
            })
    
    # Look for any JSON data in scripts
    scripts = soup.find_all('script')
    for script in scripts:
        script_content = script.string or ""
        # Look for search results data
        if 'searchResults' in script_content or 'cards' in script_content.lower():
            print(f"\nFound potential data in script tag ({len(script_content)} chars)")
            # Try to extract JSON
            json_matches = re.findall(r'\{[^{}]*"name"[^{}]*\}', script_content)
            for match in json_matches[:3]:
                print(f"  JSON snippet: {match[:100]}...")
    
    # Check page structure
    print(f"\nPage structure:")
    print(f"  - Total links: {len(card_links)}")
    
    # Look for specific card data patterns
    tables = soup.find_all('table')
    print(f"  - Tables: {len(tables)}")
    
    divs_with_class = soup.find_all('div', class_=True)
    card_divs = [d for d in divs_with_class if 'card' in str(d.get('class', '')).lower()]
    print(f"  - Divs with 'card' in class: {len(card_divs)}")
    
    # Check for specific text mentions
    caleb_mentions = html.lower().count('caleb')
    williams_mentions = html.lower().count('williams')
    cosmic_mentions = html.lower().count('cosmic')
    print(f"  - 'caleb' mentions: {caleb_mentions}")
    print(f"  - 'williams' mentions: {williams_mentions}")
    print(f"  - 'cosmic' mentions: {cosmic_mentions}")
    
    return results


def try_gemrate_api():
    """Check if Gemrate has an API we can use."""
    print("\n" + "="*60)
    print("Checking Gemrate for API endpoints")
    print("="*60)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json, text/html",
    }
    
    # Common API patterns
    api_urls = [
        "https://www.gemrate.com/api/search?q=caleb+williams+cosmic",
        "https://api.gemrate.com/search?q=caleb+williams+cosmic",
        "https://www.gemrate.com/search.json?q=caleb+williams+cosmic",
    ]
    
    with httpx.Client(timeout=30.0, headers=headers, follow_redirects=True) as client:
        for url in api_urls:
            print(f"\nTrying: {url}")
            try:
                response = client.get(url)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    print(f"Content-Type: {content_type}")
                    
                    if 'json' in content_type:
                        try:
                            data = response.json()
                            print(f"JSON response: {type(data)}")
                            if isinstance(data, dict):
                                print(f"Keys: {list(data.keys())[:5]}")
                            elif isinstance(data, list):
                                print(f"Array with {len(data)} items")
                        except:
                            print("Failed to parse as JSON")
                    else:
                        print(f"Response preview: {response.text[:200]}...")
                        
            except Exception as e:
                print(f"Error: {e}")


def examine_gemrate_homepage():
    """Get more details from Gemrate homepage to understand structure."""
    print("\n" + "="*60)
    print("Examining Gemrate Homepage Structure")
    print("="*60)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }
    
    with httpx.Client(timeout=30.0, headers=headers, follow_redirects=True) as client:
        response = client.get("https://www.gemrate.com/")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find the search form
            forms = soup.find_all('form')
            for form in forms:
                action = form.get('action', 'no action')
                method = form.get('method', 'no method')
                inputs = form.find_all('input')
                print(f"\nForm found:")
                print(f"  Action: {action}")
                print(f"  Method: {method}")
                print(f"  Inputs: {[i.get('name', 'unnamed') for i in inputs]}")
            
            # Look for navigation links to understand site structure
            nav = soup.find('nav')
            if nav:
                nav_links = nav.find_all('a')
                print(f"\nNavigation links:")
                for link in nav_links[:10]:
                    print(f"  - {link.get_text(strip=True)}: {link.get('href', 'no href')}")


def main():
    print("="*60)
    print("Gemrate.com Population Data Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print("\nTarget: 2024 Topps Cosmic Chrome Planetary Pursuit")
    print("        Caleb Williams - 'The Sun' variant")
    print("="*60)
    
    # Examine homepage first
    examine_gemrate_homepage()
    
    # Try search
    results = search_gemrate("2024 Topps Cosmic Caleb Williams")
    
    if results:
        print(f"\n{'='*60}")
        print(f"Found {len(results)} card links:")
        print("="*60)
        for r in results[:10]:
            print(f"  - {r['text'][:50]}: {r['url']}")
    
    # Try API
    try_gemrate_api()
    
    print("\n" + "="*60)
    print("Complete")
    print("="*60)


if __name__ == "__main__":
    main()
