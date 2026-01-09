import requests
from bs4 import BeautifulSoup
import re
import time
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from database import get_db_connection

BASE_URL = "https://www.sportscardspro.com/console/football-cards-2023-panini-illusions"

# Default Card Metadata
YEAR = 2023
MANUFACTURER = "Panini"
SET_NAME = "Panini Illusions"
SPORT = "Football"

def parse_title(title_text):
    """
    Parses 'C.J. Stroud [Orange] #43 /149' into components.
    Returns: (player, subset, number, print_run, is_serial)
    """
    # Clean text
    text = title_text.strip()
    
    # Regex for standard format: Name [Variant] #Number /Serial
    # \[(.*?)\] captures the variant/subset inside brackets
    # #(\S+) captures the card number
    # (?: ?/(\d+))? optionally captures the serial number
    
    # Note: Sometimes name might not have brackets if base? 
    # SCP format is fairly consistent on console pages: "Name [Subset] #Number"
    
    pattern = r"^(.*?) \[?(.*?)\]? #(\S+)(?: ?/(\d+))?"
    match = re.search(pattern, text)
    
    if match:
        player = match.group(1).strip()
        subset = match.group(2).strip()
        number = match.group(3).strip()
        print_run_str = match.group(4)
        
        is_serial = False
        print_run = None
        
        if print_run_str:
            is_serial = True
            try:
                print_run = int(print_run_str)
            except:
                pass
                
        # Clean subset if empty (Base usually has no brackets or empty content?)
        # SCP usually puts [Base] or [Retail] etc. If brackets missing, group 2 might be part of name?
        # Let's adjust regex to be greedy on name until last '[' if present.
        
        return player, subset, number, print_run, is_serial
    
    # Fallback if no match (Should rarely happen on SCP console)
    return text, "Base", "0", None, False

def scrape_set():
    conn = get_db_connection()
    cur = conn.cursor()
    
    print(f"Starting scrape for {SET_NAME} ({YEAR})...")
    
    total_cards_processed = 0
    cursor = 0
    has_more = True
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    while has_more:
        # Construct URL with cursor for pagination
        # SCP uses form posts usually, but often supports GET params on console views
        # Pattern: url?cursor=0, ?cursor=100
        url = f"{BASE_URL}?cursor={cursor}&sort=price&encoding=utf-8"
        print(f"Fetching: {url}...")
        
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                print(f"[!] Failed to fetch. Status: {resp.status_code}")
                break
                
            soup = BeautifulSoup(resp.content, "html.parser")
            
            # Select Rows - table is #games_table, distinct from other pages
            # Also, exclude headers/ads if any
            rows = soup.select("table#games_table tbody tr")
            
            if not rows:
                print("No more rows found.")
                has_more = False
                break
                
            print(f"  Found {len(rows)} cards on this page.")
            
            batch_cards_found = 0
            
            for row in rows:
                # 1. Title Parsing
                # The title is in a TD with class 'title' -> a
                title_node = row.select_one("td.title a")
                if not title_node:
                    continue
                
                full_title = title_node.text.strip()
                print(f"    Processing: {full_title}")
                
                # 2. Filter Exclusions
                if any(x in full_title.lower() for x in ["sealed", "box", "case", "pack", "lot of"]):
                    continue
                
                # 3. Parse Metadata
                player, subset, number, print_run, is_serial = parse_title(full_title)
                
                # Rookie Logic
                is_rookie = False
                if "[RC]" in full_title or row.select_one(".title span.rookie"):
                    is_rookie = True
                    
                # 4. Insert 4 Variants
                # Product ID auto-generated
                # Conflict on (player, year, set, number, subset, variant, grader, grade)
                
                variants = [
                    ("Raw", "Raw"),
                    ("PSA", "10"),
                    ("PSA", "9"),
                    ("PSA", "<9")
                ]
                
                for grader, grade in variants:
                    insert_sql = """
                        INSERT INTO cards (
                            player_name, year, set_name, subset_insert, card_number,
                            manufacturer, sport,
                            is_rookie_card, is_serial_numbered, print_run,
                            grader, grade
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """
                    cur.execute(insert_sql, (
                        player, YEAR, SET_NAME, subset, number,
                        MANUFACTURER, SPORT,
                        is_rookie, is_serial, print_run,
                        grader, grade
                    ))
                    
                batch_cards_found += 1
                
            total_cards_processed += batch_cards_found
            print(f"  > Inserted {batch_cards_found} cards from this batch. Total: {total_cards_processed}")
            conn.commit() # Commit after each page
            
            # Pagination Logic
            # If we found less than 30? Usually pages are 30, 50 or 100.
            # If 0 rows found, loop breaks above.
            # Increment cursor
            cursor += 50 # Page size is 50 based on observation
            
            # Polite Delay
            time.sleep(1)
            
        except Exception as e:
            print(f"[!] Error: {e}")
            break
            
    cur.close()
    conn.close()
    print(f"\nScrape Complete. Processed {total_cards_processed} unique cards (~{total_cards_processed*4} variants).")

if __name__ == "__main__":
    scrape_set()
