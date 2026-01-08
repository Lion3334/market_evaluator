import pandas as pd
import joblib
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from train_model import load_data, engineer_features, prepare_ml_data

MODEL_PATH_PRICE = "backend/model.pkl"
OUTPUT_PATH = "/Users/eastcoastlimited/.gemini/antigravity/brain/4a90b6ca-0bc0-4f7f-89e0-fef9d1ec5306/jayden_daniels_continuous.png"

def verify_continuous():
    print("Loading data...")
    df = load_data()
    
    print("Engineering features (for Encoders)...")
    # We run this to fit encoders and get the global dataframe shape
    df_engineered, le_player, le_parallel = engineer_features(df)
    
    # 1. Setup Target: Jayden Daniels Base Raw
    player_name = 'Jayden Daniels'
    parallel = 'Base'
    grader = 'Raw'
    
    # Filter original df for this specific card's transactions
    transactions = df_engineered[
        (df_engineered['player_name'] == player_name) & 
        (df_engineered['parallel_type'] == parallel) & 
        (df_engineered['grader'] == grader)
    ].sort_values('sale_date').copy()
    
    if transactions.empty:
        print("No transactions found.")
        return

    # 2. Create Continuous Date Range
    start_date = transactions['sale_date'].min()
    end_date = transactions['sale_date'].max() + timedelta(days=5) # Project 5 days into future
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    print(f"Generating continuous forecast for {len(date_range)} days...")
    
    # 3. Simulate Daily State
    daily_rows = []
    
    # Initial State
    last_sold_price = transactions.iloc[0]['price'] # Start with first sale
    last_sale_date = transactions.iloc[0]['sale_date']
    rolling_prices = [last_sold_price] # Keep track for rolling avg
    
    # Get Player Market Data (we need to lookup player stats for each day)
    # Ideally we'd have a lookup table for (date, player) -> (vol, avg_price)
    # We can perform a lookup on the main df_engineered
    market_lookup = df_engineered[['sale_date', 'player_name', 'player_7d_vol', 'player_7d_avg_price']].copy()
    market_lookup = market_lookup[market_lookup['player_name'] == player_name].set_index('sale_date')
    # Resample lookup to daily to handle missing days
    market_lookup = market_lookup.resample('D').first().fillna(method='ffill') 

    # Load Model
    regressor = joblib.load(MODEL_PATH_PRICE)
    
    encoded_player = le_player.transform([player_name])[0]
    encoded_parallel = le_parallel.transform([parallel])[0]
    
    # Iterate through every single day
    for current_date in date_range:
        
        # A. Check if a sale happened TODAY
        sale_today = transactions[transactions['sale_date'] == current_date]
        
        if not sale_today.empty:
            # Update state variables
            actual_price = sale_today.iloc[0]['price']
            last_sold_price = actual_price
            last_sale_date = current_date
            rolling_prices.append(actual_price)
            if len(rolling_prices) > 3: rolling_prices.pop(0)
            
            # For the prediction at this moment (Forecast for NEXT sale), we use the state *before* this sale?
            # No, continuous model predicts the "Current Fair Value".
            # If a sale happens, that IS the value.
            # But we want to predict what the model THOUGHT the price was.
            pass

        # B. Construct Feature Vector for this Day
        days_since_start = (current_date - df_engineered['sale_date'].min()).days
        days_since_last_sale = (current_date - last_sale_date).days
        
        # Calculate rolling avg 
        # (Note: strictly, the rolling avg comes from previous SALES, not previous daily predictions)
        rolling_avg_3 = sum(rolling_prices) / len(rolling_prices)
        
        # Market Stats
        try:
            m_stats = market_lookup.loc[current_date]
            p_vol = m_stats['player_7d_vol']
            p_avg = m_stats['player_7d_avg_price']
        except KeyError:
            p_vol = 0
            p_avg = 0
            
        # Features must match training order
        features = {
            'last_sold_price': last_sold_price,
            'rolling_avg_3': rolling_avg_3,
            'days_since_last_sale': days_since_last_sale,
            'player_7d_vol': p_vol,
            'player_7d_avg_price': p_avg,
            'grade_num': 0, # Raw
            'player_encoded': encoded_player,
            'parallel_encoded': encoded_parallel,
            'is_gold': 0, 'is_black': 0, 'is_rookie_num': 1, # Assumptions
            'days_since_start': days_since_start
        }
        
        # Convert to DataFrame
        X_daily = pd.DataFrame([features])
        
        # Predict
        predicted_price = regressor.predict(X_daily)[0]
        
        daily_rows.append({
            'date': current_date,
            'predicted_price': predicted_price,
            'actual_price': sale_today.iloc[0]['price'] if not sale_today.empty else None,
            'is_transaction': not sale_today.empty
        })

    # 4. Plotting
    results = pd.DataFrame(daily_rows)
    
    plt.figure(figsize=(14, 7))
    
    # A. Continuous Forecast Line
    plt.plot(results['date'], results['predicted_price'], '-', color='#d62728', linewidth=2, alpha=0.8, label='Daily Model Estimate')
    
    # B. Actual Transactions
    transactions_only = results[results['is_transaction']]
    plt.plot(transactions_only['date'], transactions_only['actual_price'], 'o', color='#1f77b4', markersize=8, label='Actual Transaction')
    
    plt.title('Jayden Daniels (Base / Raw): Continuous Daily Price Model', fontsize=14, pad=15)
    plt.ylabel('Price ($)', fontsize=12)
    plt.xlabel('Date', fontsize=12)
    plt.legend(loc='best', frameon=True)
    plt.grid(True, which='both', linestyle='--', alpha=0.3)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    plt.gcf().autofmt_xdate()
    
    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=150)
    print(f"Chart saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    verify_continuous()
