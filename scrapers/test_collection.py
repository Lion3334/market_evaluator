#!/usr/bin/env python3
"""Test script for data collection pipeline.

Tests eBay search and PSA scraping with real queries.
"""

import os
import sys
import re
from datetime import datetime
from difflib import SequenceMatcher

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(__file__))


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    text = text.lower()
    noise_words = ['the', 'a', 'an', 'card', 'rookie', 'rc', '#']
    for word in noise_words:
        text = text.replace(word, ' ')
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_grade(text: str) -> tuple:
    """Extract grade and grading company from title."""
    psa_match = re.search(r'psa\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    if psa_match:
        grade = psa_match.group(1)
        if '.' in grade:
            return f'PSA_{grade.replace(".", "_")}', 'PSA'
        return f'PSA_{grade}', 'PSA'
    
    bgs_match = re.search(r'bgs\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    if bgs_match:
        grade = bgs_match.group(1)
        return f'BGS_{grade.replace(".", "_")}', 'BGS'
    
    sgc_match = re.search(r'sgc\s*(\d+)', text, re.IGNORECASE)
    if sgc_match:
        return f'SGC_{sgc_match.group(1)}', 'SGC'
    
    if re.search(r'\braw\b|\bungraded\b', text, re.IGNORECASE):
        return 'RAW', None
    
    return None, None


# Known insert sets that should be part of set name, not parallel
KNOWN_INSERT_SETS = [
    'planetary pursuit',
    'cosmic kings',
    'cosmic queens', 
    'supernova',
    'downtown',
    'kaboom',
    'case hit',
    'color blast',
    'genesis',
    'disco',
]

# Known parallels (color variants, numbered cards)
KNOWN_PARALLELS = [
    # Cosmic insert parallels
    'the sun', 'the moon', 'the stars', 'the galaxy',
    'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto',
    # Color parallels  
    'gold', 'silver', 'bronze', 'platinum', 'ruby', 'sapphire', 'emerald', 'diamond',
    'red', 'blue', 'green', 'purple', 'orange', 'pink', 'black', 'white',
    # Chrome/Prizm parallels
    'refractor', 'xfractor', 'atomic', 'wave', 'camo', 'shimmer',
    'prizm', 'silver prizm', 'gold prizm',
    'holo', 'holofoil',
    # Rarity tiers
    'sp', 'ssp', 'sssp',
    'variation', 'variant', 'photo variation',
    # Base
    'base',
]


def extract_set_and_parallel(text: str) -> tuple:
    """Extract set name components and parallel from title.
    
    Returns:
        Tuple of (insert_set, parallel)
        - insert_set: Name of insert set if found (e.g., "Planetary Pursuit")
        - parallel: Variant name if found (e.g., "The Sun", "Gold /10")
    """
    text_lower = text.lower()
    
    insert_set = None
    parallel = None
    
    # Check for known insert sets
    for insert in KNOWN_INSERT_SETS:
        if insert in text_lower:
            insert_set = insert.title()
            break
    
    # Check for known parallels
    for par in KNOWN_PARALLELS:
        if par in text_lower:
            parallel = par.title()
            break
    
    # Check for numbered parallels like /10, /25, /99
    numbered_match = re.search(r'/(\d+)', text)
    if numbered_match:
        num = numbered_match.group(1)
        if parallel:
            parallel = f"{parallel} /{num}"
        else:
            parallel = f"/{num}"
    
    return insert_set, parallel


def analyze_query(query: str):
    """Analyze a user query to extract card attributes."""
    print(f"\n{'='*60}")
    print(f"Query Analysis")
    print(f"Input: {query}")
    print(f"{'='*60}\n")
    
    normalized = normalize_text(query)
    condition, grader = extract_grade(query)
    insert_set, parallel = extract_set_and_parallel(query)
    
    components = {
        'original_query': query,
        'detected_condition': condition,
        'detected_grader': grader,
        'insert_set': insert_set,
        'parallel': parallel,
        'is_rookie': 'rc' in query.lower() or 'rookie' in query.lower(),
    }
    
    # Extract year
    year_match = re.search(r'(20\d{2})', query)
    if year_match:
        components['year'] = int(year_match.group(1))
    
    # Player name detection (first words before keywords)
    words = query.split()
    set_keywords = ['topps', 'panini', 'mosaic', 'prizm', 'chrome', 'cosmic', 
                    'donruss', 'select', 'rc', '2024', '2023', '2022', 'planetary', 
                    'pursuit', 'the', 'sun', 'moon', 'stars']
    name_words = []
    for word in words:
        if word.lower() not in set_keywords and not word.isdigit():
            name_words.append(word)
            if len(name_words) >= 2:
                break
        else:
            break
    if name_words:
        components['player_name'] = ' '.join(name_words)
    
    # Base set detection
    base_set_keywords = ['topps', 'panini', 'donruss', 'select', 'bowman', 'upper deck']
    product_keywords = ['chrome', 'prizm', 'mosaic', 'optic', 'cosmic']
    
    base_sets = [kw for kw in base_set_keywords if kw in query.lower()]
    products = [kw for kw in product_keywords if kw in query.lower()]
    
    # Construct full set name
    set_parts = []
    if components.get('year'):
        set_parts.append(str(components['year']))
    set_parts.extend([s.title() for s in base_sets])
    set_parts.extend([p.title() for p in products])
    if insert_set:
        set_parts.append(insert_set)
    
    components['full_set_name'] = ' '.join(set_parts) if set_parts else 'Unknown'
    
    print("Extracted components:")
    print(f"  Player: {components.get('player_name', 'Unknown')}")
    print(f"  Year: {components.get('year', 'Unknown')}")
    print(f"  Set: {components.get('full_set_name', 'Unknown')}")
    print(f"  Insert: {components.get('insert_set', 'N/A')}")
    print(f"  Parallel: {components.get('parallel', 'Base')}")
    print(f"  Condition: {components.get('detected_condition', 'Unknown')}")
    print(f"  Rookie: {components.get('is_rookie', False)}")
    
    return components


def test_ebay_mock(query: str):
    """Show what eBay search would look like (without credentials)."""
    print(f"\n{'='*60}")
    print(f"eBay Search Preview")
    print(f"{'='*60}\n")
    
    if os.getenv('EBAY_APP_ID'):
        print("✓ EBAY_APP_ID found - can make real API calls")
        return True
    else:
        print("⚠️  No eBay credentials in environment")
        print("\nTo enable eBay API calls, set environment variables:")
        print("  export EBAY_APP_ID=your_app_id")
        print("  export EBAY_CERT_ID=your_cert_id")
        print("\nExpected API call:")
        print(f"  Endpoint: https://api.ebay.com/buy/browse/v1/item_summary/search")
        print(f"  Query: {query}")
        print(f"  Category: 212 (Sports Trading Cards)")
        return False


def test_psa_mock(set_name: str, player: str):
    """Show what PSA search would do."""
    print(f"\n{'='*60}")
    print(f"PSA Population Search Preview")
    print(f"{'='*60}\n")
    
    search_query = f"{set_name} Football"
    print(f"Would search PSA for: {search_query}")
    print(f"\nExpected PSA search:")
    print(f"  URL: https://www.psacard.com/pop?q={search_query.replace(' ', '+')}")
    print(f"\nLooking for:")
    print(f"  Set: {set_name}")
    print(f"  Player: {player}")


def main():
    """Run data collection tests."""
    query = "Caleb Williams RC Planetary Pursuit The Sun 2024 Topps Chrome Cosmic"
    
    print("\n" + "="*60)
    print("CardPulse Data Collection Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Step 1: Analyze the query
    components = analyze_query(query)
    
    # Step 2: Check eBay credentials
    has_ebay = test_ebay_mock(query)
    
    # Step 3: Show PSA search plan
    set_name = components.get('full_set_name', '')
    player = components.get('player_name', '')
    test_psa_mock(set_name, player)
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"\nCard identified:")
    print(f"  Player: {components.get('player_name', 'Unknown')}")
    print(f"  Year: {components.get('year', 'Unknown')}")
    print(f"  Set: {components.get('full_set_name', 'Unknown')}")
    print(f"  Parallel: {components.get('parallel', 'Base')}")
    print(f"  Rookie: {components.get('is_rookie', False)}")
    
    if not has_ebay:
        print("\n⚠️  Provide eBay API credentials to test live data collection")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
