import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from train_model import load_data, engineer_features

def debug_features():
    print("Loading data...")
    df = load_data()
    
    print("Engineering features...")
    df, _, _ = engineer_features(df)
    
    # Filter for Jayden Daniels Base Raw
    target_df = df[
        (df['player_name'] == 'Jayden Daniels') & 
        (df['parallel_type'] == 'Base') & 
        (df['grader'] == 'Raw')
    ].copy()
    
    # Filter for Dec 11 and Dec 12
    # Note: sale_date is datetime
    start_date = pd.Timestamp('2025-12-11')
    end_date = pd.Timestamp('2025-12-12')
    
    subset = target_df[
        (target_df['sale_date'] >= start_date) & 
        (target_df['sale_date'] <= end_date)
    ].sort_values('sale_date')
    
    columns_to_show = [
        'sale_date', 
        'price',
        'last_sold_price', 
        'rolling_avg_3', 
        'days_since_last_sale',
        'player_7d_vol', 
        'player_7d_avg_price',
        'days_since_start'
    ]
    
    print("\n" + "="*100)
    print("FEATURE INSPECTION: Jayden Daniels (Dec 11 - Dec 12)")
    print("="*100)
    
    # We want to see the values used to predict THIS row.
    # The 'last_sold_price' in the row is what was used to predict 'price'.
    
    for idx, row in subset.iterrows():
        print(f"Date: {row['sale_date'].date()}")
        print(f"  Target Price (Actual): ${row['price']:.2f}")
        print(f"  Inputs:")
        print(f"    Last Sold Price:     ${row['last_sold_price']:.2f}")
        print(f"    Rolling Avg (3):     ${row['rolling_avg_3']:.2f}")
        print(f"    Days Since Sale:     {row['days_since_last_sale']}")
        print(f"    Player 7D Vol:       {row['player_7d_vol']} (Sales of ALL Jayden cards)")
        print(f"    Player 7D Avg Price: ${row['player_7d_avg_price']:.2f}")
        print("-" * 50)

if __name__ == "__main__":
    debug_features()
