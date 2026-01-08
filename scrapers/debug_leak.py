import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from train_model import load_data, engineer_features

def debug_leak():
    print("Loading data...")
    df = load_data()
    
    print("Engineering features...")
    df, _, _ = engineer_features(df)
    
    # Check for Leakage
    # Leakage = last_sale_date == sale_date
    # If using 'shift(1)' on a date-sorted list where dates are identical (or same day),
    # the shifts might pick up same-day data.
    
    # We want to see rows where `last_sale_date` (which we created in recent update) is the SAME DAY as `sale_date`.
    
    # Note: df['last_sale_date'] was added in the previous turn. 
    # Let's inspect rows with multiple sales on same day.
    
    # Find a day with > 1 transaction for Jayden Base Raw
    target = df[
        (df['player_name'] == 'Jayden Daniels') & 
        (df['parallel_type'] == 'Base') & 
        (df['grader'] == 'Raw')
    ].copy()
    
    # Count per day
    daily_counts = target.groupby('sale_date').size()
    multi_sale_days = daily_counts[daily_counts > 1]
    
    if multi_sale_days.empty:
        print("No multi-transaction days found for Jayden Daniels Base Raw to verify.")
        # Try finding ANY variant
        all_counts = df.groupby(['variant_id', 'sale_date']).size()
        multi_days = all_counts[all_counts > 1]
        if multi_days.empty:
            print("No multi-tx days in entire dataset.")
            return
        # Pick one
        vid, date = multi_days.index[0]
        print(f"Checking Variant: {vid} on {date}")
        subset = df[(df['variant_id'] == vid) & (df['sale_date'] == date)]
    else:
        date = multi_sale_days.index[0]
        print(f"Checking Jayden Base Raw on {date}")
        subset = target[target['sale_date'] == date]
    
    print(f"\nTransactions on {date}:")
    for idx, row in subset.iterrows():
        print(f"Sale ID: {idx}")
        print(f"  Price: ${row['price']}")
        print(f"  Last Sold Price (Feature): ${row['last_sold_price']}")
        
        # In strict daily lag, Last Sold Price should be identical for ALL same-day transactions
        # because they all reference Yesterday's Close.
        print("-" * 30)

if __name__ == "__main__":
    debug_leak()
