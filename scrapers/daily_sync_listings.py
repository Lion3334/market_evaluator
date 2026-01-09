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

from fetch_active_listings import save_active_listings

def main():
    print(f"\n{'='*50}")
    print(f"Daily Sync Started: {datetime.now().isoformat()}")
    print(f"{'='*50}\n")
    
    try:
        save_active_listings()
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
