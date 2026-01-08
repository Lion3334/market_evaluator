import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, precision_score, recall_score
from sklearn.preprocessing import LabelEncoder
import joblib
import os

DB_NAME = "cardpulse"
MODEL_PATH_PRICE = "backend/model.pkl"
MODEL_PATH_DIRECTION = "backend/model_direction.pkl"

def load_data():
    """Load transaction data from PostgreSQL V2 Schema."""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        conn = psycopg2.connect(db_url)
    else:
        conn = psycopg2.connect(database=DB_NAME)
        
    # Join sales and cards. We want granular sales data.
    query = """
        SELECT 
            s.price,
            s.sale_date,
            s.grade,
            s.grader,
            c.product_id,
            c.player_name,
            c.year,
            c.set_name,
            c.parallel_type,
            c.is_rookie_card
        FROM sales s
        JOIN cards c ON s.product_id = c.product_id
        WHERE s.price IS NOT NULL
        ORDER BY s.sale_date ASC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def engineer_features(df):
    """Create features for ML model including Lag Features and Spillover."""
    df = df.copy()
    df['sale_date'] = pd.to_datetime(df['sale_date'])
    
    # 1. Define Variant (Product + Grade + Grader)
    df['variant_id'] = (
        df['product_id'].astype(str) + "_" + 
        df['grader'].fillna("Unk") + "_" + 
        df['grade'].fillna("Unk")
    )
    
    # 2. Sort by Variant and Date
    df = df.sort_values(['variant_id', 'sale_date'])
    
    # 3. Calculate Strict Daily Lags (Previous Day's Closing Price)
    # Goal: Try to predict TODAY'S price using ONLY data from YESTERDAY (and prior).
    # No intraday leakage allowed.
    
    # A. Get Daily Closing Price for each variant
    daily_close = df.groupby(['variant_id', 'sale_date'])['price'].last().reset_index()
    
    feature_chunks = []
    
    for vid, group in daily_close.groupby('variant_id'):
        group = group.set_index('sale_date').sort_index()
        
        # 1. Calculate "True Strict Previous Date" (For Staleness)
        # Shift the raw dates BEFORE resampling to capture the last *actual* sale
        # This gives us: On Dec 12, prev strict date is Dec 5.
        group['strict_prev_date'] = group.index.to_series().shift(1)
        
        # 2. Resample to Daily (fill gaps)
        # We need this to exist for every target day in df
        daily = group.resample('D').ffill()
        
        # 3. Shift Prices (The "Close" of Today becomes "Prev Close" for Tomorrow)
        daily['prev_day_close'] = daily['price'].shift(1)
        
        # 4. Rolling Average of strict daily closes (using shifted values)
        daily['rolling_avg_3'] = daily['prev_day_close'].rolling(window=3, min_periods=1).mean()
        
        daily['variant_id'] = vid
        feature_chunks.append(daily[['variant_id', 'prev_day_close', 'strict_prev_date', 'rolling_avg_3']])
        
    daily_features = pd.concat(feature_chunks).reset_index()
    
    # D. Merge back to main DF
    # We merge on (variant_id, sale_date). 
    df = pd.merge(df, daily_features, on=['variant_id', 'sale_date'], how='left')
    
    # Rename for compatibility
    df['last_sold_price'] = df['prev_day_close']
    df['days_since_last_sale'] = (df['sale_date'] - df['strict_prev_date']).dt.days
    
    # Cleanup
    df = df.drop(columns=['prev_day_close', 'strict_prev_date'], errors='ignore')
    
    # Let's clean up staleness:
    # We'll use the 'last_sale_date' from the ORIGINAL shift logic (which found the previous transaction), 
    # BUT we must enforce that if last_sale_date == sale_date, we look back further.
    # Actually, easier: Just define 'last_sale_date' as the date of the 'last_sold_price' we just found. 
    # Since we ffilled, we don't know the exact date it originated. 
    # Let's stick to the user's core request: "Price forecast... incorporating only Dec 11 and prior".
    # Using 'prev_day_close' satisfies this perfectly.
    # For staleness: `(sale_date - last_REAL_transaction_prior_to_today)`.
    
    # Let's re-do staleness strictly:
    # 1. Group by Variant
    # 2. Iterate and find 'max(date) WHERE date < current_row.date'
    # This is efficiently done by: `shift()` on daily_aggregated data.
    
    # We already have `daily_close` (Daily transactions).
    # If we shift THAT, we get the real last transaction date.
    
    real_last_date = []
    for vid, group in daily_close.groupby('variant_id'):
        group = group.set_index('sale_date').sort_index()
        # Don't resample yet, just shift the available dates
        # If dates are [Dec 1, Dec 5, Dec 12]
        # Shift 1 -> [NaN, Dec 1, Dec 5]
        # So on Dec 12, the "strict prev date" is Dec 5.
        group['strict_prev_date'] = group.index.to_series().shift(1)
        
        # Now we need to broadcast this to the "filled" days?
        # Or just merge this "True Last Date" to the transaction dates.
        # But wait, if we have gaps, we need ffill for the gaps.
        
        # Resample to Daily to fill the gap days (Dec 6, Dec 7...) with "Dec 5".
        group = group.resample('D').ffill() 
        # ffill propagates "Dec 5" to Dec 6...Dec 11.
        
        # On Dec 12, the row exists in daily_close? Yes.
        # So on Dec 12, `strict_prev_date` is Dec 5. Correct.
        
        group['variant_id'] = vid
        real_last_date.append(group[['variant_id', 'strict_prev_date']])
        
    dates_df = pd.concat(real_last_date).reset_index()
    df = pd.merge(df, dates_df, on=['variant_id', 'sale_date'], how='left')
    
    df['days_since_last_sale'] = (df['sale_date'] - df['strict_prev_date']).dt.days
    
    # Cleanup
    df = df.drop(columns=['prev_day_close', 'strict_prev_date', 'last_sale_date'], errors='ignore')
    
    # Rolling Average (Strict)
    # We can just take the rolling of the DAILY CLOSE (shifted)
    # Since we already have daily_close_resampled with `prev_day_close`
    # We can perform rolling on that.
    
    # Re-using the first loop is cleaner... but let's just make `rolling_avg_3` off the `last_sold_price`.
    # `last_sold_price` is a daily series (merged).
    # BUT `last_sold_price` in `df` has duplicates for same day.
    # We should calculate rolling on the `daily_lags` DF before merging.
    
    # Let's refine step B above.
    pass # Placeholder for replace logic context
    
    # Drop rows where we don't have history
    df = df.dropna(subset=['last_sold_price'])
    
    print(f"  Data after dropping first sales (Lag setup): {len(df)} rows")
    
    # --- Player Market Features (Cross-Variant Spillover) ---
    daily_player_stats = df.groupby(['player_name', 'sale_date']).agg(
        daily_vol=('price', 'count'),
        daily_rev=('price', 'sum')
    ).reset_index()
    
    player_dfs = []
    for player, p_data in daily_player_stats.groupby('player_name'):
        p_data = p_data.drop(columns=['player_name'], errors='ignore').set_index('sale_date').sort_index()
        p_data = p_data.resample('D').sum().fillna(0)
        shifted = p_data.shift(1)
        rolling_7d = shifted.rolling('7D', min_periods=1).sum()
        
        rolling_7d['player_7d_vol'] = rolling_7d['daily_vol']
        rolling_7d['player_7d_avg_price'] = rolling_7d['daily_rev'] / rolling_7d['daily_vol'].replace(0, np.nan)
        rolling_7d['player_7d_avg_price'] = rolling_7d['player_7d_avg_price'].fillna(0)
        
        rolling_7d['player_name'] = player
        player_dfs.append(rolling_7d.reset_index())
        
    market_features = pd.concat(player_dfs)
    
    df = pd.merge(df, market_features[['sale_date', 'player_name', 'player_7d_vol', 'player_7d_avg_price']], 
                  on=['sale_date', 'player_name'], how='left')
                  
    df['player_7d_vol'] = df['player_7d_vol'].fillna(0)
    df['player_7d_avg_price'] = df['player_7d_avg_price'].fillna(0)
    
    # --- Standard Features ---
    def map_grade(row):
        g = str(row['grade']).upper()
        if 'RAW' in g: return 0
        if '10' in g: return 10
        if '9' in g: return 9
        if '8' in g: return 8
        if '7' in g: return 7
        return 0 
        
    df['grade_num'] = df.apply(map_grade, axis=1)
    
    le_parallel = LabelEncoder()
    df['parallel_encoded'] = le_parallel.fit_transform(df['parallel_type'].fillna("Base"))
    
    df['is_gold'] = df['parallel_type'].apply(lambda x: 1 if x == 'Gold' else 0)
    df['is_black'] = df['parallel_type'].apply(lambda x: 1 if x == 'Black' else 0)
    
    le_player = LabelEncoder()
    df['player_encoded'] = le_player.fit_transform(df['player_name'])
    
    df['is_rookie_num'] = df['is_rookie_card'].apply(lambda x: 1 if x else 0)
    
    min_date = df['sale_date'].min()
    df['days_since_start'] = (df['sale_date'] - min_date).dt.days
    
    return df, le_player, le_parallel

def prepare_ml_data(df):
    """Prepare X and targets for training."""
    feature_cols = [
        'last_sold_price',     
        'rolling_avg_3',
        'days_since_last_sale',  
        'player_7d_vol',       
        'player_7d_avg_price', 
        'grade_num', 
        'player_encoded', 
        'parallel_encoded',
        'is_gold', 'is_black',
        'is_rookie_num',
        'days_since_start'
    ]
    
    # Ensure strict time sorting before returning features
    df = df.sort_values('sale_date')
    
    X = df[feature_cols].fillna(0)
    y_price = df['price']
    
    # Directional Target: 1 if Next Price > Last Sold Price, else 0
    y_direction = (df['price'] > df['last_sold_price']).astype(int)
    
    return X, y_price, y_direction, df['sale_date']

def train_and_evaluate():
    """Train Regressor and Classifier models using Time Series Validation."""
    print("=" * 60)
    print("CARD PRICE & DIRECTION MODEL TRAINING (TIME SERIES)")
    print("=" * 60)
    
    print("\n[1/4] Loading data...")
    df = load_data()
    print(f"  Loaded {len(df)} transactions")
    
    if len(df) < 10: return

    print("\n[2/4] Engineering features...")
    df, le_player, le_parallel = engineer_features(df)
    
    # Sort strictly by date before splitting
    df = df.sort_values('sale_date')
    X, y_price, y_direction, dates = prepare_ml_data(df)
    print(f"  Features: {list(X.columns)}")
    
    # --- TIME SERIES SPLIT ---
    # We train on the PAST (first 80%) and test on the FUTURE (last 20%)
    split_idx = int(len(X) * 0.8)
    
    print("\n[3/4] Splitting data (Time-Series Split)...")
    split_date = dates.iloc[split_idx]
    print(f"  Training Range: {dates.iloc[0].date()} -> {dates.iloc[split_idx-1].date()}")
    print(f"  Testing Range:  {split_date.date()} -> {dates.iloc[-1].date()}")
    
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    yp_train, yp_test = y_price.iloc[:split_idx], y_price.iloc[split_idx:]
    yd_train, yd_test = y_direction.iloc[:split_idx], y_direction.iloc[split_idx:]
    
    # --- 1. PRICE REGRESSOR ---
    print("\n[4/4] Training Models...")
    print("\n  A. Price Regressor (Gradient Boosting)...")
    regressor = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
    regressor.fit(X_train, yp_train)
    
    yp_pred = regressor.predict(X_test)
    mae = mean_absolute_error(yp_test, yp_pred)
    r2 = r2_score(yp_test, yp_pred)
    print(f"    MAE: ${mae:.2f}")
    print(f"    R²:  {r2:.3f}")
    
    # --- 2. DIRECTION CLASSIFIER ---
    print("\n  B. Direction Classifier (Gradient Boosting)...")
    classifier = GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42)
    classifier.fit(X_train, yd_train)
    
    yd_pred = classifier.predict(X_test)
    acc = accuracy_score(yd_test, yd_pred)
    prec = precision_score(yd_test, yd_pred)
    rec = recall_score(yd_test, yd_pred)
    
    print(f"    Accuracy:  {acc:.1%}")
    print(f"    Precision: {prec:.1%} (Correctly predicted 'Up')")
    print(f"    Recall:    {rec:.1%} (Caught actual 'Ups')")
    
    # Save Models
    print("\nSaving models...")
    os.makedirs(os.path.dirname(MODEL_PATH_PRICE), exist_ok=True)
    
    joblib.dump(regressor, MODEL_PATH_PRICE)
    joblib.dump(classifier, MODEL_PATH_DIRECTION)
    
    joblib.dump(le_player, "backend/le_player.pkl")
    joblib.dump(le_parallel, "backend/le_parallel.pkl")
    print("Done!")

if __name__ == "__main__":
    train_and_evaluate()
