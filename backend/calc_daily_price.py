
import os
import argparse
from datetime import date, timedelta
import pandas as pd
import numpy as np
from database import get_db_connection

# Configurable Parameters (can be overridden by args or env)
DEFAULT_SUPPLY_SHOCK_MULTIPLIER = 1.5
DEFAULT_SHOCK_DISCOUNT = 0.05       # 5% discount
DEFAULT_BO_DISCOUNT = 0.85          # 15% discount for Best Offer Listings

def calc_daily_price(target_date=None, shock_multiplier=DEFAULT_SUPPLY_SHOCK_MULTIPLIER):
    if target_date is None:
        target_date = date.today()
        
    print(f"Calculating Market Price for {target_date}...")
    print(f"  Shock Multiplier: {shock_multiplier}x")
    
    conn = get_db_connection()
    
    # 1. Fetch Daily Supply Metrics (Current + History for Moving Avg)
    print("Fetching supply metrics...")
    start_history = target_date - timedelta(days=7)
    
    query_supply = """
        SELECT date, product_id, 
               new_count_fixed_price_only + new_count_best_offer as new_count_bin,
               median_new_price
        FROM daily_supply_metrics
        WHERE date >= %s AND date <= %s
    """
    df_supply = pd.read_sql(query_supply, conn, params=(start_history, target_date))
    
    # 2. Fetch Current Active Floor Prices
    # We want the MIN price per product_id where types are Fixed/BIN
    print("Fetching active inventory floors...")
    query_floor = """
        SELECT product_id, MIN(price) as floor_price
        FROM active_listings
        WHERE (buying_options LIKE '%FIXED_PRICE%' OR buying_options LIKE '%BIN%')
        AND is_ignored = FALSE
        GROUP BY product_id
    """
    df_floor = pd.read_sql(query_floor, conn)
    
    if df_supply.empty or df_floor.empty:
        print("No data found. Ensure calc_daily_supply has run and listings exist.")
        return

    # Process per Product
    # Get list of products involved today (either have new supply OR have active inventory)
    today_supply = df_supply[df_supply['date'] == target_date]
    active_pids = set(df_floor['product_id'].unique())
    new_pids = set(today_supply['product_id'].unique())
    all_pids = active_pids.union(new_pids)
    
    results = []
    
    for pid in all_pids:
        # A. Inputs
        try:
            floor_row = df_floor[df_floor['product_id'] == pid]
            p_floor = floor_row['floor_price'].iloc[0] if not floor_row.empty else None
            
            supply_rows = df_supply[df_supply['product_id'] == pid]
            supply_today = supply_rows[supply_rows['date'] == target_date]
            
            p_new = supply_today['median_new_price'].iloc[0] if not supply_today.empty else None
            v_new = supply_today['new_count_bin'].iloc[0] if not supply_today.empty else 0
            
            # Calc V_avg (7 day trail)
            v_avg = supply_rows['new_count_bin'].mean() if not supply_rows.empty else 0
            
            # Logic
            mv_est = None
            driving_factor = 'None'
            signal = 'Low'
            
            # Step A: Base MV
            if p_floor and p_new:
                if p_new < p_floor:
                    mv_est = p_new
                    driving_factor = 'New Low'
                    signal = 'High'
                else:
                    mv_est = p_floor
                    driving_factor = 'Floor'
                    signal = 'Medium'
            elif p_floor:
                mv_est = p_floor
                driving_factor = 'Floor (No New)'
                signal = 'Medium'
            elif p_new:
                mv_est = p_new
                driving_factor = 'New Only (No Floor)'
                signal = 'Low' # Risky
            
            # Step B: Supply Shock
            shock_active = False
            if mv_est and v_avg > 0:
                if v_new > (shock_multiplier * v_avg):
                    shock_active = True
                    mv_est = mv_est * (1.0 - DEFAULT_SHOCK_DISCOUNT)
                    driving_factor += ' + Shock'
                    
            if mv_est:
                results.append((
                    target_date,
                    int(pid),
                    float(mv_est),
                    'v1_supply_velocity',
                    False, # used_implied_sales (Placeholder)
                    float(shock_multiplier) if shock_active else None,
                    signal,
                    driving_factor
                ))
                
        except Exception as e:
            print(f"Error processing PID {pid}: {e}")
            continue
            
    # Insert
    print(f"Computed prices for {len(results)} products.")
    if results:
        cur = conn.cursor()
        insert_sql = """
            INSERT INTO price_history (
                date, product_id, estimated_market_value, model_version, 
                used_implied_sales, supply_shock_multiplier, signal_strength, driving_factor
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cur.executemany(insert_sql, results)
            conn.commit()
            print("Successfully saved price estimates.")
        except Exception as e:
            conn.rollback()
            print(f"Error saving to DB: {e}")
        finally:
            cur.close()
    
    conn.close()

if __name__ == "__main__":
    calc_daily_price()
