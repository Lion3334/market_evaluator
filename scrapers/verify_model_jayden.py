import pandas as pd
import joblib
import sys
import os

# Add local directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from train_model import load_data, engineer_features, prepare_ml_data

MODEL_PATH_PRICE = "backend/model.pkl"
MODEL_PATH_DIRECTION = "backend/model_direction.pkl"

def verify_jayden():
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
    
    if target_df.empty:
        print("No data found!")
        return

    # Sort by date
    target_df = target_df.sort_values('sale_date')
    
    # Prepare X
    X, y_actual, y_direction_actual = prepare_ml_data(target_df)
    
    # Load Models
    print("Loading models...")
    regressor = joblib.load(MODEL_PATH_PRICE)
    classifier = joblib.load(MODEL_PATH_DIRECTION)
    
    # Predict
    y_pred_price = regressor.predict(X)
    y_pred_dir = classifier.predict(X)
    y_prob_dir = classifier.predict_proba(X)[:, 1] # Prob of class 1 (Up)
    
    # Create comparison table
    results = target_df[['sale_date', 'price', 'last_sold_price']].copy()
    results['predicted_price'] = y_pred_price
    results['predicted_dir'] = y_pred_dir
    results['prob_up'] = y_prob_dir
    results['actual_dir'] = y_direction_actual
    
    # Determine correctness
    results['dir_correct'] = results['predicted_dir'] == results['actual_dir']
    
    # Format for display
    print("\n" + "="*110)
    print("TIME SERIES VERIFICATION: Jayden Daniels (Base / Raw) - DUAL FORECAST")
    print("="*110)
    # Header
    print(f"{'Date':<12} {'Prev':>8} {'Actual':>8} {'Fcst $':>8} {'Diff':>8} | {'Act Dir':<8} {'Pred Dir':<8} {'Prob Up':>8} {'Correct?':<8}")
    print("-" * 110)
    
    correct_count = 0
    total_count = 0
    
    for idx, row in results.iterrows():
        date_str = row['sale_date'].strftime('%Y-%m-%d')
        actual = row['price']
        prev = row['last_sold_price']
        pred_price = row['predicted_price']
        diff = pred_price - actual
        
        # Direction Logic
        act_d_str = "UP" if row['actual_dir'] == 1 else "DOWN/EQ"
        pred_d_str = "UP" if row['predicted_dir'] == 1 else "DOWN/EQ"
        prob = row['prob_up']
        is_correct = "YES" if row['dir_correct'] else "NO"
        
        if row['dir_correct']: correct_count += 1
        total_count += 1
        
        print(f"{date_str:<12} ${prev:>7.0f} ${actual:>7.0f} ${pred_price:>7.0f} ${diff:>7.0f} | {act_d_str:<8} {pred_d_str:<8} {prob:>7.0%} {is_correct:<8}")

    print("-" * 110)
    print(f"Directional Accuracy: {correct_count}/{total_count} ({correct_count/total_count:.1%})")

if __name__ == "__main__":
    verify_jayden()
