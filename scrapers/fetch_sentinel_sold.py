
import os
import requests
from bs4 import BeautifulSoup
import time
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from database import get_db_connection
from datetime import datetime

# Set Map (Expand as needed)
SET_URLS = {
    "Panini Illusions": "https://www.sportscardspro.com/console/football-cards-2023-panini-illusions"
}

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

def backfill_urls(conn):
    print("Checking for missing Sentinel URLs...")
    cur = conn.cursor()
    # Find sets with missing URLs
    cur.execute("""
        SELECT DISTINCT set_name 
        FROM cards 
        WHERE is_sentinel = TRUE AND url IS NULL
    """)
    sets = cur.fetchall()
    
    for (set_name,) in sets:
        url = SET_URLS.get(set_name)
        if not url:
            print(f"Skipping unknown set: {set_name}")
            continue
            
        print(f"Backfilling URLs for set: {set_name} from {url}")
        resp = requests.get(url, headers=get_headers())
        if resp.status_code != 200:
            print(f"Failed to load set page: {resp.status_code}")
            continue
            
        soup = BeautifulSoup(resp.content, "html.parser")
        rows = soup.select("table#games_table tbody tr")
        
        updates = []
        # Strategy: Get all sentinels for this set
        cur.execute("SELECT product_id, player_name, card_number FROM cards WHERE set_name = %s AND is_sentinel = TRUE AND url IS NULL", (set_name,))
        sentinels = cur.fetchall()
        
        for pid, player, number in sentinels:
            # Find row in HTML that contains player and number
            for row in rows:
                row_text = row.text.lower()
                clean_player = player.lower().split('[')[0].strip() # Remove variant from name if present
                
                if clean_player in row_text:
                    link = row.select_one("td.title a")
                    if link:
                        href = "https://www.sportscardspro.com" + link['href']
                        updates.append((href, pid))
                        break # Found it
        
        if updates:
            print(f"Applying {len(updates)} URL backfills...")
            cur.executemany("UPDATE cards SET url = %s WHERE product_id = %s", updates)
            conn.commit()
            
    cur.close()

def scrape_sentinel_sales():
    conn = get_db_connection()
    
    # 1. Ensure URLs
    backfill_urls(conn)
    
    # 2. Scrape Sales
    cur = conn.cursor()
    cur.execute("SELECT product_id, url, player_name, grader, grade FROM cards WHERE is_sentinel = TRUE AND url IS NOT NULL")
    sentinels = cur.fetchall()
    
    print(f"Scraping sales for {len(sentinels)} sentinels...")
    
    for pid, url, player, grader, grade in sentinels:
        # Construct variant string for heuristic matching
        variant_str = f"{grader} {grade}"
        print(f"Checking {player} [{variant_str}]: {url}")

        try:
            resp = requests.get(url, headers=get_headers())
            if resp.status_code != 200:
                continue
                
            soup = BeautifulSoup(resp.content, "html.parser")
            
            # Determine SCP Tab Class based on Variant
            # Mappings derived from SCP HTML structure:
            # Raw -> completed-auctions-used
            # PSA 10 -> completed-auctions-manual-only (Labeled PSA 10)
            # Grade 9 -> completed-auctions-graded
            # Grade 8 -> completed-auctions-new
            
            scp_class = "completed-auctions-used" # Default to Raw
            g_low = grader.lower()
            gr_str = str(grade)
            
            if g_low == 'psa':
                if gr_str == '10':
                    scp_class = "completed-auctions-manual-only"
                elif gr_str == '9':
                    scp_class = "completed-auctions-graded"
                elif gr_str == '8':
                    scp_class = "completed-auctions-new"
            elif g_low == 'raw':
                scp_class = "completed-auctions-used"
                
            # Select table inside the specific tab/div
            selector = f"div.{scp_class} table.hoverable-rows tbody tr"
            sales_rows = soup.select(selector)
            
            print(f"  Selector: {selector}")
            print(f"  Found {len(sales_rows)} rows.")
            
            if not sales_rows:
                # Debug print
                pass
                
            for row in sales_rows[:5]: # just recent 5
                try:
                    date_cell = row.select_one("td.date")
                    price_cell = row.select_one("td.numeric span.js-price") # Updated selector based on HTML inspection
                    
                    if not date_cell:
                        print("    Skipping row: No date cell")
                        continue
                        
                    date_str = date_cell.text.strip() # "2025-10-11"
                    
                    if not price_cell:
                        print("    Skipping row: No price cell")
                        continue
                        
                    price_str = price_cell.text.strip().replace('$','').replace(',','')
                    try:
                        price = float(price_str)
                    except:
                        print(f"    Skipping row: Invalid price {price_str}")
                        continue
                    
                    title_cell = row.select_one("td.title a")
                    title = title_cell.text.strip() if title_cell else "Unknown"
                    
                    # Store (No heuristic match needed if we found the correct table!)
                    print(f"    Found Sale: {date_str} - ${price} - {title[:30]}...")
                    cur.execute("""
                        INSERT INTO sentinel_sales (product_id, sold_date, price, source, title)
                        VALUES (%s, %s, %s, 'SportsCardsPro', %s)
                        ON CONFLICT DO NOTHING
                    """, (pid, date_str, price, title))
                        
                except Exception as e:
                    print(f"    Error parsing row: {e}")
            
            conn.commit() # Commit after processing all rows for a sentinel
            time.sleep(1) # polite delay
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            
    cur.close()
    conn.close()
    print("Sentinel scrape complete.")

if __name__ == "__main__":
    scrape_sentinel_sales()
