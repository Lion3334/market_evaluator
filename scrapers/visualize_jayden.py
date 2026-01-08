import pandas as pd
import joblib
import sys
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Add local directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from train_model import load_data, engineer_features, prepare_ml_data

MODEL_PATH = "backend/model.pkl"
OUTPUT_PATH = "/Users/eastcoastlimited/.gemini/antigravity/brain/4a90b6ca-0bc0-4f7f-89e0-fef9d1ec5306/jayden_daniels_forecast.png"

def visualize_jayden():
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
    X, y_actual = prepare_ml_data(target_df)
    
    # Load Model
    print("Loading model...")
    model = joblib.load(MODEL_PATH)
    
    # Predict
    y_pred = model.predict(X)
    
    # Create results df
    results = target_df[['sale_date', 'price']].copy()
    results['predicted_price'] = y_pred
    
    # Plotting
    print("Generating plot...")
    plt.figure(figsize=(14, 7))
    
    # Plot Actual
    plt.plot(results['sale_date'], results['price'], 'o-', label='Actual Sale Price', color='#1f77b4', linewidth=2, markersize=6, alpha=0.7)
    
    # Plot Forecast
    plt.plot(results['sale_date'], results['predicted_price'], 'x--', label='Model Forecast (Predicted Next Sale)', color='#d62728', linewidth=1.5, markersize=6)
    
    plt.title('Jayden Daniels Downtown (Base / Raw): Actual vs Model Forecast', fontsize=14, pad=15)
    plt.ylabel('Price ($)', fontsize=12)
    plt.xlabel('Date', fontsize=12)
    
    # Formatting
    plt.legend(loc='best', frameon=True, fontsize=10)
    plt.grid(True, which='both', linestyle='--', alpha=0.3)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=3))
    plt.gcf().autofmt_xdate()
    
    # Annotate the outlier
    outlier_date = pd.Timestamp('2026-01-05')
    outlier_val = 396
    
    # Find exact row if helpful, or just annotate roughly
    plt.annotate('Outlier ($396)\nModel ignored ->', 
                 xy=(outlier_date, outlier_val), 
                 xytext=(outlier_date - pd.Timedelta(days=5), outlier_val - 50),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6))

    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=150)
    print(f"Plot saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    visualize_jayden()
