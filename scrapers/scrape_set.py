#!/usr/bin/env python3
"""
Scrape SportsCardPro Set Console.
Usage: python3 scrape_set.py <URL>
Example: python3 scrapers/scrape_set.py "https://www.sportscardspro.com/console/football-cards-2023-panini-donruss-downtown"

Fetches:
1. List of cards in the set.
2. Metadata (Year, Set Name from title).
3. Detailed transaction history for each card (Deep Dive).
"""

import httpx
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime
import time
import random
import re
import sys
import argparse

# Constants
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

def extract_set_metadata(soup):
    """Extract Year, Sport, Manufacturer, Set Name from page title/headers."""
    # Title format often: "Prices for 2023 Panini Donruss Downtown Football Cards"
    h1 = soup.select_one("h1")
    title = h1.text.strip() if h1 else ""
    
    print(f"Page Title: {title}")
    
    # 1. Year
    year = 2024 # Default
    year_match = re.search(r'\b(19|20)\d{2}\b', title)
    if year_match:
        year = int(year_match.group(0))
        
    # 2. Sport
    sport = "Web"
    if "Football" in title: sport = "Football"
    elif "Basketball" in title: sport = "Basketball"
    elif "Baseball" in title: sport = "Baseball"
    elif "Soccer" in title: sport = "Soccer"
    elif "Hockey" in title: sport = "Hockey"
    elif "Pokemon" in title: sport = "Pokemon"
    
    # 3. Manufacturer (Simple guess)
    manu = "Unknown"
    if "Panini" in title: manu = "Panini"
    elif "Topps" in title: manu = "Topps"
    elif "Bowman" in title: manu = "Bowman"
    elif "Leaf" in title: manu = "Leaf"
    elif "Upper Deck" in title: manu = "Upper Deck"
    elif "Fleer" in title: manu = "Fleer"
    
    # 4. Set Name (The whole string between Year and Sport basically)
    # e.g. "2023 Panini Donruss Downtown Football" -> "Panini Donruss Downtown"
    # This is a bit fuzzy, so we'll store the clean title minus "Prices for" and "Cards"
    clean_title = title.replace("Prices for ", "").replace("Cards", "").strip()
    # Remove Sport from end if present
    clean_title = re.sub(f"{sport}$", "", clean_title, flags=re.IGNORECASE).strip()
    # Remove Year from start
    clean_title = re.sub(f"^{year}", "", clean_title).strip()
    
    set_name = clean_title # e.g. "Panini Donruss Downtown"
    
    # Attempt to split Subset if possible (e.g. "Donruss Downtown")
    subset = "Base"
    if "Downtown" in set_name:
        subset = "Downtown"
        # Optional: remove Downtown from set_name to keep it clean? 
        # For now, keeping full name in set_name is safer for unique constraints match
        # set_name = set_name.replace("Downtown", "").strip() 
    
    print(f"Extracted Metadata: Year={year}, Sport={sport}, Manu={manu}, Set={set_name}, Subset={subset}")
    
    return {
        "year": year,
        "sport": sport,
        "manufacturer": manu,
        "set_name": set_name,
        "subset": subset
    }

def scrape_set_list(url):
    """Scrape the console page for all cards in the set."""
    print(f"Scanning set page: {url}")
    soup = get_soup(url, "lxml")
    if not soup: return [], {}
    
    metadata = extract_set_metadata(soup)
    cards = []
    
    # Strategy 1: Find specific table class
    table = soup.select_one("table.js-items")
    
    # Strategy 2: Find ANY table with 'Card' header
    if not table:
        print("Explicit 'table.js-items' not found. Searching all tables...")
        for t in soup.find_all("table"):
            headers = [th.text.strip() for th in t.find_all("th")]
            if "Card" in headers and "Ungraded" in headers:
                table = t
                print("Found matching table by headers.")
                break
    
    # Parse Table
    if table:
        rows = table.select("tbody tr")
        print(f"Found {len(rows)} rows in table.")
        for row in rows:
            link_tag = row.select_one("td a") # Match first link in any column usually
            if not link_tag:
                # Try finding by title class
                link_tag = row.select_one("td.title a")
                
            if link_tag:
                name_full = link_tag.text.strip()
                href = link_tag["href"]
                # Ensure it's a product link
                if "/game/" not in href: continue
                
                # Fix double URL: href might be absolute or relative
                if href.startswith("http"):
                    card_url = href
                else:
                    card_url = BASE_URL + href
                
                # Parse Number
                match = re.search(r'^(.*?) #(\d+\w?(-\d+)?)$', name_full)
                if match:
                    player = match.group(1)
                    number = match.group(2)
                else:
                    player = name_full
                    number = "N/A"
                
                cards.append({
                    "player": player,
                    "number": number,
                    "url": card_url,
                    "metadata": metadata
                })
    
    # Strategy 3: HTML Fallback (Scan all links)
    if not cards:
        print("Table strategy failed. Scanning all links...")
        links = soup.find_all("a", href=True)
        seen_urls = set()
        
        for link in links:
            href = link["href"]
            if "/game/" in href:
                if href.startswith("http"):
                    full_url = href
                else:
                    full_url = BASE_URL + href

                if full_url in seen_urls: continue
                seen_urls.add(full_url)
                
                text = link.text.strip()
                if not text or "Collection" in text or "Wishlist" in text: continue

                match = re.search(r'^(.*?) #(\d+\w?(-\d+)?)$', text)
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
                    "metadata": metadata
                })

    print(f"Found {len(cards)} cards in set.")
    return cards

def scrape_card_details(card_url):
    """Scrape individual card page for prices and detailed attributes."""
    soup = get_soup(card_url, "lxml")
    if not soup:
        return None, None, {}

    # 1. Prices (Robust text search)
    ungraded_price = None
    psa10_price = None
    
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
        "is_rookie": False,
        "epid": None,
        "card_number": None,
        "sales_data": {"raw": [], "psa10": [], "psa9": []}
    }
    
    # Helper to parse sales table
    def parse_sales_table(container_class, target_grade=None):
        sales = []
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

                            if target_grade:
                                if target_grade not in title_text.upper():
                                    continue
                                    
                            sales.append({"date": date_str, "price": price, "title": title_text})
                        except:
                            continue
        return sales

    details['sales_data']['raw'] = parse_sales_table("completed-auctions-used")
    all_graded = parse_sales_table("completed-auctions-graded")
    manual_psa10 = parse_sales_table("completed-auctions-manual-only", "PSA 10")
    
    for sale in all_graded:
        title = sale['title'].upper()
        if "PSA 10" in title:
            details['sales_data']['psa10'].append(sale)
        elif "PSA 9" in title:
             details['sales_data']['psa9'].append(sale)
             
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
            if not title_td or not val_td: continue
            
            label = title_td.text.strip().lower()
            val_text = val_td.text.strip()
            
            if "rookie card" in label: # "Is Rookie Card:"
                details["is_rookie"] = "yes" in val_text.lower()
            elif "epid" in label:
                details["epid"] = val_text
            elif "card number" in label:
                details["card_number"] = val_text

    return ungraded_price, psa10_price, details

def save_to_db(cards_data):
    """Save scraped data to PostgreSQL V2 Schema."""
    if not cards_data: return
    
    try:
        conn = psycopg2.connect(database=DB_NAME)
        cur = conn.cursor()
        
        for card in cards_data:
            details = card.get('details', {})
            meta = card['metadata'] # Generic metadata from extraction
            
            player_name = card['player']
            year = meta['year']
            manufacturer = meta['manufacturer']
            set_name = meta['set_name']
            subset = meta['subset']
            
            card_number = details.get('card_number') or card['number']
            
            # Parallels logic (Basic)
            parallel_type = "Base"
            if "[Gold]" in player_name:
                parallel_type = "Gold"
                player_name = player_name.replace("[Gold]", "").strip()
            elif "[Black]" in player_name:
                parallel_type = "Black"
                player_name = player_name.replace("[Black]", "").strip()
            player_name = re.sub(r'\[.*?\]', '', player_name).strip()
            
            sport = meta['sport']
            is_rookie = details.get('is_rookie', False)
            epid = details.get('epid')
            
            # Insert Product (Cards table)
            # The schema has a UNIQUE constraint on:
            # (player_name, year, set_name, card_number, subset_insert, parallel_type, variation_type, grader, grade)
            
            cur.execute("""
                INSERT INTO cards (
                    sport, year, manufacturer, set_name, subset_insert, 
                    player_name, card_number, parallel_type, is_rookie_card, 
                    epid, url, variation_type, grader, grade
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Raw', 'Raw')
                ON CONFLICT (player_name, year, set_name, card_number, subset_insert, parallel_type, variation_type, grader, grade)
                DO UPDATE SET 
                    epid = EXCLUDED.epid,
                    url = EXCLUDED.url
                RETURNING product_id
            """, (
                sport, year, manufacturer, set_name, subset, 
                player_name, card_number, parallel_type, is_rookie, 
                epid, card['url'], "Base" # Default variation_type
            ))
            
            product_id = cur.fetchone()[0]
            
            # Insert Sales
            sales_data = details.get('sales_data', {})
            
            # Helper to insert list of sales
            def insert_sales(sales_list, grade_str, grader_str):
                for sale in sales_list:
                    try:
                        sale_date = datetime.strptime(sale['date'], '%Y-%m-%d')
                    except:
                        sale_date = datetime.now()
                    
                    # Unique ID: Source + Product + Date + Price
                    txn_id = f"SCP_{grader_str}{grade_str}_{product_id}_{sale['date']}_{str(sale['price']).replace('.','')}"
                    
                    cur.execute("""
                        INSERT INTO sales (
                            transaction_id, product_id, price, sale_date, 
                            grader, grade, source, title
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (transaction_id, source) DO NOTHING
                    """, (
                        txn_id, product_id, sale['price'], sale_date,
                        grader_str, grade_str, 'SportsCardPro', sale['title']
                    ))

            insert_sales(sales_data.get('raw', []), 'Raw', 'Raw')
            insert_sales(sales_data.get('psa10', []), '10', 'PSA')
            insert_sales(sales_data.get('psa9', []), '9', 'PSA')
                
        conn.commit()
        cur.close()
        conn.close()
        print("Database update complete.")
        
    except Exception as e:
        print(f"Database Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Scrape a Sportscardpro Set Page")
    parser.add_argument("url", help="URL of the set console page")
    args = parser.parse_args()
    
    print(f"Starting Scraper for: {args.url}")
    
    # 1. Get List & Metadata
    cards = scrape_set_list(args.url)
    
    if not cards:
        print("No cards found.")
        sys.exit(1)
        
    # 2. Iterate and Details
    full_data = []
    print(f"Scraping details for {len(cards)} cards...")
    
    for i, card in enumerate(cards):
        print(f"Processing {i+1}/{len(cards)}: {card['player']}")
        try:
            raw, psa10, details = scrape_card_details(card['url'])
            card['raw_price'] = raw
            card['psa10_price'] = psa10
            card['details'] = details
            full_data.append(card)
        except Exception as e:
            print(f"Error processing {card['player']}: {e}")
        
        time.sleep(random.uniform(1.0, 2.0))
        
    # 3. Save
    save_to_db(full_data)
    print("Done!")

if __name__ == "__main__":
    main()
