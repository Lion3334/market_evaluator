#!/usr/bin/env python3
"""
Scrape SportsCardPro for 2024 Panini Donruss Downtown cards.
Fetches Raw and PSA 10 data and populates the database.
"""

import httpx
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime
import time
import random
import re

# Constants
SET_URL = "https://www.sportscardspro.com/console/football-cards-2024-panini-donruss-downtown"
BASE_URL = "https://www.sportscardspro.com"
DB_NAME = "cardpulse"

def get_soup(url, parser="html.parser"):
    """Fetch URL and return BeautifulSoup object."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = httpx.get(url, headers=headers, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        return BeautifulSoup(response.text, parser)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_price(price_str):
    """Parse price string like '$1,234.56' to float 1234.56"""
    if not price_str or 'N/A' in price_str:
        return None
    try:
        # Remove '$', ',', and whitespace
        clean = re.sub(r'[^\d.]', '', price_str)
        return float(clean)
    except:
        return None

def scrape_set_list():
    """Scrape the console page for all cards in the set."""
    print(f"Scanning set page: {SET_URL}")
    soup = get_soup(SET_URL, "html.parser")
    # ... (rest of function is same, but soup is now lxml)
    if not soup: return []
    
    cards = []
    # Fallback: Find all links that look like card details
    # URL Pattern: /game/football-cards-2024-panini-donruss-downtown/
    
    # Try the table first
    rows = soup.select("table.js-items tbody tr")
    if rows:
        print(f"Found {len(rows)} rows in table.")
        for row in rows:
            link_tag = row.select_one("td.title a")
            if link_tag:
                name_full = link_tag.text.strip()
                url = BASE_URL + link_tag["href"]
                # Parse name
                match = re.search(r'^(.*?) #(\d+\w?)$', name_full)
                if match:
                    player = match.group(1)
                    number = match.group(2)
                else:
                    player = name_full
                    number = "N/A"
                
                cards.append({
                    "player": player,
                    "number": number,
                    "url": url,
                    "set_name": "2024 Panini Donruss Downtown",
                    "year": 2024
                })
    
    # If table failed or empty, try all links
    if not cards:
        print("Table selector failed. Scanning all links...")
        links = soup.find_all("a", href=True)
        seen_urls = set()
        
        for link in links:
            href = link["href"]
            if "/game/football-cards-2024-panini-donruss-downtown/" in href:
                full_url = BASE_URL + href
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                
                text = link.text.strip()
                if not text: continue
                
                # Filter out "Collection" or "Wishlist" links if they share the URL
                if "Collection" in text or "Wishlist" in text:
                    continue

                # Parse name
                match = re.search(r'^(.*?) #(\d+\w?)$', text)
                if match:
                    player = match.group(1)
                    number = match.group(2)
                else:
                    player = text
                    number = "N/A"
                    
                cards.append({
                    "player": player,
                    "number": number,
                    "url": full_url,
                    "set_name": "2024 Panini Donruss Downtown",
                    "year": 2024
                })
        
    print(f"Found {len(cards)} cards in set.")
    if len(cards) == 0:
        print("DEBUG: Dumping first 1000 chars of HTML:")
        print(soup.prettify()[:2000])
        # Check for specific failure modes
        if "CAPTCHA" in soup.text:
            print("DEBUG: Hit CAPTCHA")
        if "login" in soup.text.lower():
            print("DEBUG: Hit Login Wall")
    return cards

def scrape_card_details(card_url):
    """Scrape individual card page for prices and detailed attributes."""
    soup = get_soup(card_url, "lxml")
    if not soup:
        return None, None, {}

    # 1. Prices (Robust text search)
    ungraded_price = None
    psa10_price = None
    
    # ... (keep existing simple price parsing) ...
    tds = soup.find_all("td")
    for td in tds:
        text = td.text.strip()
        if "Ungraded" == text:
            price_td = td.find_next("td", class_="price")
            if price_td: ungraded_price = parse_price(price_td.text.strip())
        elif "PSA 10" == text:
            price_td = td.find_next("td", class_="price")
            if price_td: psa10_price = parse_price(price_td.text.strip())

    if not ungraded_price:
        used_td = soup.find("td", id="used_price")
        if used_td:
            price_span = used_td.select_one(".price")
            if price_span: ungraded_price = parse_price(price_span.text.strip())

    # 2. Detailed Metadata
    details = {
        "base_set": None, "genre": None, "is_rookie": False,
        "epid": None, "card_number": None,
        "sales_data": {"raw": [], "psa10": [], "psa9": []}
    }
    
    # Helper to parse sales table
    def parse_sales_table(container_class, target_grade=None):
        sales = []
        # Find all divs with this class (sometimes duplicates)
        containers = soup.find_all("div", class_=container_class)
        for container in containers:
            table = container.find("table")
            if table:
                rows = table.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 3:
                        try:
                            date_str = cols[0].text.strip()
                            title_td = row.find("td", class_="title")
                            title_text = title_td.text.strip() if title_td else ""
                            price_str = row.find("span", class_="js-price").text.strip()
                            
                            price = parse_price(price_str)
                            if not price: continue

                            # Filter if target_grade is specified
                            if target_grade:
                                # Loose check for grade in title
                                if target_grade not in title_text.upper():
                                    continue
                                    
                            sales.append({"date": date_str, "price": price, "title": title_text})
                        except:
                            continue
        return sales

    # Parse Raw Sales (completed-auctions-used)
    details['sales_data']['raw'] = parse_sales_table("completed-auctions-used")
    
    # Parse Graded Sales (completed-auctions-graded)
    # We will split these into PSA 10 and PSA 9 based on title
    all_graded = parse_sales_table("completed-auctions-graded")
    
    # Backup: Check manual-only for PSA 10 specifically if graded is empty or as supplement
    manual_psa10 = parse_sales_table("completed-auctions-manual-only", "PSA 10")
    
    for sale in all_graded:
        title = sale['title'].upper()
        if "PSA 10" in title:
            details['sales_data']['psa10'].append(sale)
        elif "PSA 9" in title:
             details['sales_data']['psa9'].append(sale)
             
    # Add manual only if not present (simple dedup by date+price)
    existing_10_keys = {f"{s['date']}_{s['price']}" for s in details['sales_data']['psa10']}
    for sale in manual_psa10:
        key = f"{sale['date']}_{sale['price']}"
        if key not in existing_10_keys and "PSA 10" in sale['title'].upper():
             details['sales_data']['psa10'].append(sale)

    attr_table = soup.select_one("table#attribute")
    if attr_table:
        for row in attr_table.select("tr"):
            title_td = row.select_one("td.title")
            val_td = row.select_one("td.details")
            if not title_td or not val_td:
                continue
                
            label = title_td.text.strip().lower()
            val_text = val_td.text.strip()
            
            if "base set" in label:
                details["base_set"] = val_text
            elif "genre" in label:
                details["genre"] = val_text
            elif "rookie card" in label: # "Is Rookie Card:"
                details["is_rookie"] = "yes" in val_text.lower()
            elif "epid" in label:
                # Value might be numeric text
                details["epid"] = val_text
            elif "card number" in label: # "Card Number:" or itemprop="model-number"
                details["card_number"] = val_text

    return ungraded_price, psa10_price, details

def save_to_db(cards_data):
    """Save scraped data to PostgreSQL V2 Schema."""
    try:
        conn = psycopg2.connect(database=DB_NAME)
        cur = conn.cursor()
        
        for card in cards_data:
            details = card.get('details', {})
            
            # Map scraped data to V2 Schema columns
            # Product ID is internal SERIAL, so we just insert unique attributes
            
            # 1. Attributes
            player_name = card['player']
            year = 2024
            set_name = "Panini Donruss" # Base set name is usually the manufacturer/brand
            subset_insert = "Downtown"
            card_number = details.get('card_number') or card['number']
            
            # Check for Parallels
            # We scrape [Gold], [Black] from title if present
            parallel_type = "Base"
            if "[Gold]" in player_name:
                parallel_type = "Gold"
                player_name = player_name.replace("[Gold]", "").strip()
            elif "[Black]" in player_name:
                parallel_type = "Black"
                player_name = player_name.replace("[Black]", "").strip()
            # Clean generic brackets
            player_name = re.sub(r'\[.*?\]', '', player_name).strip()
            
            # SportsCardPro doesn't give us sport directly usually, but we scraped "Genre" -> Football Cards
            sport = "Football"
            if "Basketball" in str(details.get('genre')): sport = "Basketball"
            elif "Baseball" in str(details.get('genre')): sport = "Baseball"
            
            is_rookie = details.get('is_rookie', False)
            epid = details.get('epid')
            
            # Insert Product (Cards table)
            # UNIQUE(player_name, year, set_name, card_number, subset_insert, parallel_type, variation_type)
            # We use ON CONFLICT to get the product_id
            
            cur.execute("""
                INSERT INTO cards (
                    sport, year, manufacturer, set_name, subset_insert, 
                    player_name, card_number, parallel_type, is_rookie_card, 
                    epid, url
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (player_name, year, set_name, card_number, subset_insert, parallel_type, variation_type)
                DO UPDATE SET 
                    epid = EXCLUDED.epid,
                    url = EXCLUDED.url
                RETURNING product_id
            """, (
                sport, year, "Panini", set_name, subset_insert, 
                player_name, card_number, parallel_type, is_rookie, 
                epid, card['url']
            ))
            
            product_id = cur.fetchone()[0]
            
            # 2. Insert Historical Sales (Granular)
            # details['sales_data'] contains lists for 'raw' and 'psa10'
            
            sales_data = details.get('sales_data', {})
            
            # --- Insert RAW Sales ---
            for sale in sales_data.get('raw', []):
                # Composite ID: SCP_RAW_{product_id}_{date}_{price} (Add price/hash to be unique if multiple same day)
                # Better: Use the date + price as unique key since we don't have a true txn ID from SCP easily without parsing links
                # Let's clean the date first. format matches '2024-01-01'
                try:
                    sale_date = datetime.strptime(sale['date'], '%Y-%m-%d')
                except:
                    sale_date = datetime.now() # Fallback
                
                txn_id = f"SCP_RAW_{product_id}_{sale['date']}_{str(sale['price']).replace('.','')}"
                
                cur.execute("""
                    INSERT INTO sales (
                        transaction_id, product_id, price, sale_date, 
                        grader, grade, source, title
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (transaction_id, source) DO NOTHING
                """, (
                    txn_id, product_id, sale['price'], sale_date,
                    'Raw', 'Raw', 'SportsCardPro', 'Historical Sale'
                ))
                
            # --- Insert PSA 10 Sales ---
            for sale in sales_data.get('psa10', []):
                try:
                    sale_date = datetime.strptime(sale['date'], '%Y-%m-%d')
                except:
                    sale_date = datetime.now()
                    
                txn_id = f"SCP_PSA10_{product_id}_{sale['date']}_{str(sale['price']).replace('.','')}"
                
                cur.execute("""
                    INSERT INTO sales (
                        transaction_id, product_id, price, sale_date, 
                        grader, grade, source, title
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (transaction_id, source) DO NOTHING
                """, (
                    txn_id, product_id, sale['price'], sale_date,
                    'PSA', '10', 'SportsCardPro', 'Historical Sale'
                ))
                
            # --- Insert PSA 9 Sales ---
            for sale in sales_data.get('psa9', []):
                try:
                    sale_date = datetime.strptime(sale['date'], '%Y-%m-%d')
                except:
                    sale_date = datetime.now()
                    
                txn_id = f"SCP_PSA9_{product_id}_{sale['date']}_{str(sale['price']).replace('.','')}"
                
                cur.execute("""
                    INSERT INTO sales (
                        transaction_id, product_id, price, sale_date, 
                        grader, grade, source, title
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (transaction_id, source) DO NOTHING
                """, (
                    txn_id, product_id, sale['price'], sale_date,
                    'PSA', '9', 'SportsCardPro', 'Historical Sale'
                ))
                
        conn.commit()
        cur.close()
        conn.close()
        print("Database update complete (V2 Schema).")
        
    except Exception as e:
        print(f"Database Error: {e}")

def main():
    print("Starting SportsCardPro Scraper...")
    
    # 1. Get List
    cards = scrape_set_list()
    
    # 2. Iterate and Details
    full_data = []
    print(f"Scraping details for {len(cards)} cards...")
    
    for i, card in enumerate(cards):
        print(f"Processing {i+1}/{len(cards)}: {card['player']}")
        
        raw, psa10, details = scrape_card_details(card['url'])
        
        card['raw_price'] = raw
        card['psa10_price'] = psa10
        card['details'] = details
        full_data.append(card)
        
        # Polite delay
        time.sleep(random.uniform(1.0, 2.0))
        
    # 3. Save
    save_to_db(full_data)
    print("Done!")

if __name__ == "__main__":
    main()
