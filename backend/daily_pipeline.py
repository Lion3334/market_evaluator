
import subprocess
import os
import sys
from datetime import datetime

# Path helper
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPERS_DIR = os.path.join(BACKEND_DIR, '..', 'scrapers')

def run_script(script_path, label):
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] >>> Starting {label}...")
    try:
        # We use sys.executable to ensure we use the same python env
        result = subprocess.run([sys.executable, script_path], check=True, capture_output=False)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] <<< {label} Complete.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[!] Error running {label}: {e}")
        return False

def daily_pipeline():
    print("="*60)
    print(f"Starting Daily Market Pipeline at {datetime.now()}")
    print("="*60)
    
    # 1. Calculate Daily Supply Metrics
    # (Inputs: Active Listings which should have been updated by 8am job)
    if not run_script(os.path.join(BACKEND_DIR, 'calc_daily_supply.py'), "Supply Metrics Calculation"):
        print("Pipeline Aborted at Supply Metrics.")
        return

    # 2. Run Sentinel Assignment (Refresh to ensure we track the right cards)
    run_script(os.path.join(BACKEND_DIR, 'assign_sentinels.py'), "Sentinel Assignment")

    # 3. Run Price Model
    if not run_script(os.path.join(BACKEND_DIR, 'calc_daily_price.py'), "Daily Price Model"):
        print("Pipeline Aborted at Price Model.")
        return

    # 4. Scrape Sentinel Sales (Ground Truth)
    # Note: Scrapers dir needs to be in path or handled correctly
    run_script(os.path.join(SCRAPERS_DIR, 'fetch_sentinel_sold.py'), "Sentinel Sales Scraper")

    # 5. Validation & Reporting
    # This will now generate the report artifact
    run_script(os.path.join(BACKEND_DIR, 'validate_model.py'), "Validation & Reporting")
    
    print("\n" + "="*60)
    print("Pipeline Execution Finished.")
    print("="*60)

if __name__ == "__main__":
    daily_pipeline()
