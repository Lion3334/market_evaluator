#!/usr/bin/env python3
"""
Daily Sync Script for Active Listings
Run via cron: 0 6 * * * cd /path/to/project && python3 scrapers/daily_sync_listings.py >> logs/sync.log 2>&1
"""
import sys
import os
from datetime import datetime

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.append(os.path.dirname(__file__))

from fetch_active_by_set import save_listings_for_set

# Define monitored sets (add more as needed)
MONITORED_SETS = [
    {"set_name": "Panini Illusions", "query": "2023 Panini Illusions"},
    {"set_name": "Panini Donruss", "query": "2024 Panini Donruss Downtown"},
]

def main():
    print(f"\n{'='*50}")
    print(f"Daily Sync Started: {datetime.now().isoformat()}")
    print(f"{'='*50}\n")
    
    try:
        # 1. Fetch Active Listings by SET (Efficient)
        print("[Step 1] Fetching Active Listings (Set-Level)...")
        for set_config in MONITORED_SETS:
            save_listings_for_set(set_config["set_name"], set_config["query"])
        
        # 2. Calculate Daily Supply Metrics
        print(f"\n[Step 2] Calculating Daily Supply Metrics...")
        from backend.calc_daily_supply import calculate_daily_supply
        calculate_daily_supply()

        print(f"\n{'='*50}")
        print(f"Daily Sync Completed: {datetime.now().isoformat()}")
        print(f"{'='*50}\n")
    except Exception as e:
        print(f"[ERROR] Sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
