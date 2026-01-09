import argparse
from datetime import datetime, date
from database import get_db_connection
import pandas as pd

def calculate_daily_supply(target_date=None):
    """
    Calculates supply metrics for a given date and upserts them into daily_supply_metrics.
    Default date is today.
    """
    if target_date is None:
        target_date = date.today()
    
    print(f"Calculating supply metrics for {target_date}...")
    
    conn = get_db_connection()
    
    # We fetch ALL active listings to process in memory (pandas is efficient for this scale ~3k rows)
    # Filter 1: Total Active Depth (Active on or before target_date)
    # Note: Using survivor bias (current active_listings table)
    query_active = """
        SELECT product_id, price, buying_options, start_date 
        FROM active_listings 
        WHERE product_id IS NOT NULL 
        AND is_ignored = FALSE
    """
    df = pd.read_sql(query_active, conn)
    
    # Ensure date handling
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['start_date_only'] = df['start_date'].dt.date
    
    # --- logic ---
    # 1. New Listings (start_date == target_date)
    new_mask = (df['start_date_only'] == target_date)
    df_new = df[new_mask].copy()
    
    # 2. Total Active (start_date <= target_date)
    # (Assuming items active today provided they started before or on today)
    active_mask = (df['start_date_only'] <= target_date)
    df_active = df[active_mask].copy()
    
    # Helper to classify type
    def get_type(options):
        # normalize
        opts = str(options).upper()
        if 'AUCTION' in opts:
            return 'AUCTION'
        elif 'BEST_OFFER' in opts: # Fixed Price + Best Offer
            return 'BEST_OFFER'
        elif 'FIXED_PRICE' in opts: # Fixed Price Only (Strict)
            return 'FIXED_PRICE_ONLY'
        return 'UNKNOWN'

    df_new['type'] = df_new['buying_options'].apply(get_type)
    df_active['type'] = df_active['buying_options'].apply(get_type)
    
    # --- Aggregation ---
    
    # Get unique products
    product_ids = df['product_id'].unique()
    
    metrics_list = []
    
    for pid in product_ids:
        # Filter matches
        new_subset = df_new[df_new['product_id'] == pid]
        active_subset = df_active[df_active['product_id'] == pid]
        
        # Counts: New
        new_counts = new_subset['type'].value_counts()
        nc_fp = new_counts.get('FIXED_PRICE_ONLY', 0)
        nc_bo = new_counts.get('BEST_OFFER', 0)
        nc_au = new_counts.get('AUCTION', 0)
        
        # Counts: Active
        active_counts = active_subset['type'].value_counts()
        ta_fp = active_counts.get('FIXED_PRICE_ONLY', 0)
        ta_bo = active_counts.get('BEST_OFFER', 0)
        ta_au = active_counts.get('AUCTION', 0)
        
        # Median Price (New Fixed Price Only + Best Offer, Excluding Auctions)
        # Filter for non-auction types
        price_subset = new_subset[new_subset['type'].isin(['FIXED_PRICE_ONLY', 'BEST_OFFER'])]
        median_price = 0
        if not price_subset.empty:
            median_price = price_subset['price'].median()
            
        metrics_list.append((
            target_date, 
            int(pid), 
            int(nc_fp), int(nc_bo), int(nc_au),
            int(ta_fp), int(ta_bo), int(ta_au),
            float(median_price) if not pd.isna(median_price) else None
        ))
        
    print(f"Computed metrics for {len(metrics_list)} products.")
    
    # --- Insert/Upsert ---
    cur = conn.cursor()
    
    upsert_sql = """
        INSERT INTO daily_supply_metrics (
            date, product_id, 
            new_count_fixed_price_only, new_count_best_offer, new_count_auction,
            total_active_fixed_price_only, total_active_best_offer, total_active_auction,
            median_new_price
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (product_id, date) DO UPDATE SET
            new_count_fixed_price_only = EXCLUDED.new_count_fixed_price_only,
            new_count_best_offer = EXCLUDED.new_count_best_offer,
            new_count_auction = EXCLUDED.new_count_auction,
            total_active_fixed_price_only = EXCLUDED.total_active_fixed_price_only,
            total_active_best_offer = EXCLUDED.total_active_best_offer,
            total_active_auction = EXCLUDED.total_active_auction,
            median_new_price = EXCLUDED.median_new_price,
            updated_at = CURRENT_TIMESTAMP;
    """
    
    cur.executemany(upsert_sql, metrics_list)
    conn.commit()
    cur.close()
    conn.close()
    print("Database updated successfully.")

if __name__ == "__main__":
    calculate_daily_supply()
