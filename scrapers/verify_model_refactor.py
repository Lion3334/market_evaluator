import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from train_model import prepare_ml_data

def test_time_series_split():
    print("TEST: Verifying Time Series Split Logic...")
    
    # 1. Create Mock Data (100 days descending/scrambled to test sorting)
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(100)]
    # Shuffle them to ensure our logic sorts them
    np.random.shuffle(dates)
    
    df = pd.DataFrame({
        'sale_date': dates,
        'price': np.random.rand(100) * 100,
        'last_sold_price': np.random.rand(100) * 90,
        # Add required dummy columns
        'rolling_avg_3': 0, 'days_since_last_sale': 0, 'player_7d_vol': 0,
        'player_7d_avg_price': 0, 'grade_num': 10, 'player_encoded': 1,
        'parallel_encoded': 0, 'is_gold': 0, 'is_black': 0, 'is_rookie_num': 1,
        'days_since_start': 0
    })
    
    # 2. Run the preparation
    # (It should sort by date inside)
    X, y_price, y_direction, out_dates = prepare_ml_data(df)
    
    # 3. Verify Sorting
    if not out_dates.is_monotonic_increasing:
        print("FAIL: Dates are not sorted strictly increasing!")
        return
        
    print("PASS: Data successfully sorted by date.")
    
    # 4. Verify Split Logic
    split_idx = int(len(X) * 0.8)
    train_dates = out_dates.iloc[:split_idx]
    test_dates = out_dates.iloc[split_idx:]
    
    max_train = train_dates.max()
    min_test = test_dates.min()
    
    print(f"Max Train Date: {max_train.date()}")
    print(f"Min Test Date:  {min_test.date()}")
    
    if max_train < min_test:
        print("PASS: NO DATA LEAKAGE. Training ends strictly before Testing begins.")
    else:
        print("FAIL: DATA LEAKAGE DETECTED.")

if __name__ == "__main__":
    test_time_series_split()
