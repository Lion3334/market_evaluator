#!/usr/bin/env python3
"""Process scraped eBay sold listings for Drake Maye Rookie Kings."""

import json
import re
from datetime import datetime

# Raw data from browser subagent
raw_data = [
  {
    "title": "2024 Panini Donruss Optic - Rookie Kings Drake Maye #3 (RC) PSA 10",
    "price": "$745.00 (+$5.15 delivery)",
    "date": "Jan 5, 2026"
  },
  {
    "title": "2024 Donruss Optic Drake Maye Rookie Kings #3 PSA 10! SSP! CASE HIT! 📈🔥",
    "price": "$661.00 (+$4.87 delivery)",
    "date": "Jan 5, 2026"
  },
  {
    "title": "2024 Panini Donruss Optic - Rookie Kings Drake Maye #3 (RC)",
    "price": "$690.00 (+$5.15 delivery)",
    "date": "Jan 5, 2026"
  },
  {
    "title": "2024 Donruss Optic - Rookie Kings Drake Maye #3 (RC)",
    "price": "$650.00 (+$4.76 delivery)",
    "date": "Jan 4, 2026"
  },
  {
    "title": "2024 Panini Donruss Optic Rookie Kings Drake Maye #3 CASE HIT SSP",
    "price": "$350.00 (+$8.40 delivery)",
    "date": "Jan 4, 2026"
  },
  {
    "title": "2024 Donruss Optic Drake Maye Rookie Kings RC Rookie #3 Patriots PSA 10",
    "price": "$594.00 (+$5.20 delivery)",
    "date": "Jan 3, 2026"
  },
  {
    "title": "2024 Panini Donruss Optic - Rookie Kings Drake Maye #3 (RC)",
    "price": "$300.00 (+$4.95 delivery)",
    "date": "Jan 2, 2026"
  },
  {
    "title": "2024 Panini Donruss Optic Rookie Kings Drake Maye #3 CASE HIT SSP",
    "price": "$300.00 (+$4.95 delivery)",
    "date": "Jan 1, 2026"
  },
  {
    "title": "2024 Panini Donruss Optic - Rookie Kings Drake Maye #3 (RC) PSA 10",
    "price": "$749.00 (+$8.40 delivery)",
    "date": "Dec 30, 2025"
  },
  {
    "title": "2024 Panini Donruss Optic Rookie Kings Drake Maye #3 CASE HIT SSP",
    "price": "$300.00 (+$4.54 delivery)",
    "date": "Dec 30, 2025"
  },
  {
    "title": "2024 Panini DonRuss Optic Drake Maye Rookie Kings #3 RC PSA 10 SSP Patriots 🔥",
    "price": "$720.00 (+$7.95 delivery)",
    "date": "Dec 29, 2025"
  },
  {
    "title": "2024 Donruss Optic Drake Maye Rookie Kings RC Black Pandora #13/25 PSA 10",
    "price": "$3,383.00 (+$4.99 delivery)",
    "date": "Dec 26, 2025"
  },
  {
    "title": "2024 Panini Optic Drake Maye Rookie Kings SSP Case Hit #3",
    "price": "$375.00 (+$5.15 delivery)",
    "date": "Dec 24, 2025"
  },
  {
    "title": "2024 Donruss Optic Drake Maye Rookie Kings RC Rookie #3 Patriots",
    "price": "$223.50 (+$4.99 delivery)",
    "date": "Dec 23, 2025"
  },
  {
    "title": "2024 Panini Donruss Optic Rookie Kings Drake Maye #3 MINT GRADEABLE CASE HIT SSP",
    "price": "$300.00 (+$5.15 delivery)",
    "date": "Dec 22, 2025"
  },
  {
    "title": "2024 Panini Donruss Optic Drake Maye Rookie Kings #3",
    "price": "$300.00 (+$5.15 delivery)",
    "date": "Dec 22, 2025"
  },
  {
    "title": "2024 Donruss Optic DRAKE MAYE Rookie Kings 🔥CASE HIT 🔥 PATRIOTS 🔥 MVP",
    "price": "$270.00 (+$4.65 delivery)",
    "date": "Dec 21, 2025"
  },
  {
    "title": "2024 PANINI DONRUSS OPTIC ROOKIE KINGS #3 DRAKE MAYE ROOKIE RC PSA 7",
    "price": "$202.50 (+$5.99 delivery)",
    "date": "Dec 21, 2025"
  },
  {
    "title": "2024 Panini Donruss Optic Drake Maye ROOKIE Kings Black Pandora /25 PSA 10 D1",
    "price": "$3,375.00 (+$40.00 delivery)",
    "date": "Dec 18, 2025"
  },
  {
    "title": "2024 Panini Donruss Optic - Rookie Kings Drake Maye #3 (RC)",
    "price": "$299.00 (+$4.54 delivery)",
    "date": "Dec 17, 2025"
  }
]

def clean_price(price_str):
    # Remove shipping text (keep just the base price for consistent comparison)
    # The browser agent combined them, but let's just take the first dollar amount
    # Example: "$745.00 (+$5.15 delivery)" -> 745.00
    try:
        # Match the first dollar amount
        match = re.search(r'\$?([\d,]+\.?\d*)', price_str)
        if match:
            return float(match.group(1).replace(',', ''))
        return 0.0
    except:
        return 0.0

def detect_condition(title):
    title_lower = title.lower()
    if re.search(r'psa\s*10', title_lower):
        return 'PSA_10'
    if re.search(r'psa\s*9', title_lower):
        return 'PSA_9'
    return 'RAW'

def is_valid_base_card(title):
    title_lower = title.lower()
    # Exclude known parallels if they are not the base insert
    exclude_terms = ['pandora', 'gold', 'green', 'blue', '/25', '/10', '/5', 'auto', 'signed']
    for term in exclude_terms:
        if term in title_lower:
            return False
    return True

def main():
    print("=" * 80)
    print("HISTORICAL SALES DATA (Drake Maye Rookie Kings #3)")
    print("Cleaned & Organized by Grade")
    print("=" * 80)
    
    organized = {'RAW': [], 'PSA_9': [], 'PSA_10': []}
    
    for item in raw_data:
        if not is_valid_base_card(item['title']):
            continue
            
        condition = detect_condition(item['title'])
        price = clean_price(item['price'])
        
        # Filter check: one of the "Raw" items was $690 and $650 which seems high for Raw (base is ~300)
        # item 3: "2024 Panini Donruss Optic - Rookie Kings Drake Maye #3 (RC)" price $690
        # item 4: "2024 Donruss Optic - Rookie Kings Drake Maye #3 (RC)" price $650
        # Wait, PSA 10 is ~700. If RAW is 650, maybe it is graded but not in title? 
        # Or maybe price spike? Or maybe a different card?
        # Let's keep them for now but flag if outlier.
        
        if condition in organized:
            organized[condition].append({
                'date': item['date'],
                'price': price,
                'title': item['title']
            })
    
    # Calculate stats and print
    for grade in ['RAW', 'PSA_9', 'PSA_10']:
        items = organized[grade]
        if not items:
            print(f"\n[{grade}] - No sales found")
            continue
            
        avg_price = sum(i['price'] for i in items) / len(items)
        min_price = min(i['price'] for i in items)
        max_price = max(i['price'] for i in items)
        
        print(f"\n[{grade}]")
        print(f"  Sales Found: {len(items)}")
        print(f"  Average:     ${avg_price:.2f}")
        print(f"  Range:       ${min_price:.2f} - ${max_price:.2f}")
        print("-" * 80)
        
        for item in items:
            print(f"  {item['date']:<12} | ${item['price']:>7.2f} | {item['title'][:55]}...")

if __name__ == "__main__":
    main()
