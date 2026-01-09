
import pandas as pd
import numpy as np
from datetime import date
from database import get_db_connection

def validate_model():
    print("Validating Model Performance...")
    conn = get_db_connection()
    
    # 1. Fetch Sales (Ground Truth)
    # Filter to recent sales that might have overlapping estimates
    query_sales = """
        SELECT product_id, sold_date, price as actual_price
        FROM sentinel_sales
        ORDER BY sold_date DESC
    """
    df_sales = pd.read_sql(query_sales, conn)
    
    if df_sales.empty:
        print("No sentinel sales found yet. Run fetch_sentinel_sold.py first.")
        return

    # 2. Fetch Estimates (Model Output)
    query_est = """
        SELECT product_id, date, estimated_market_value as predicted_price, model_version
        FROM price_history
    """
    df_est = pd.read_sql(query_est, conn)
    
    if df_est.empty:
        print("No price estimates found. Run calc_daily_price.py first.")
        return
        
    # 3. Merge
    # We want to match Sale on Date D with Estimate on Date D (or D-1 if D missing?)
    # Stick to exact date match for strict validation context.
    
    # Convert dates to datetime/date objects if needed
    df_sales['date'] = pd.to_datetime(df_sales['sold_date']).dt.date
    df_est['date'] = pd.to_datetime(df_est['date']).dt.date
    
    merged = pd.merge(df_sales, df_est, on=['product_id', 'date'], how='inner')
    
    print(f"Matched {len(merged)} sales to daily estimates.")
    
    if len(merged) < 1:
        print("Not enough matched data points for significant validation.")
        return
        

    # 4. Metrics
    merged['error'] = merged['predicted_price'] - merged['actual_price']
    merged['abs_error'] = merged['error'].abs()
    merged['pct_error'] = (merged['abs_error'] / merged['actual_price']) * 100
    
    rmse = np.sqrt((merged['error'] ** 2).mean())
    mae = merged['abs_error'].mean()
    bias = merged['error'].mean()
    mape = merged['pct_error'].mean()
    
    # Hit Rate (within 15%)
    hits = len(merged[merged['pct_error'] <= 15])
    hit_rate = (hits / len(merged)) * 100
    
    # Generate Report Content
    report_lines = []
    report_lines.append(f"# Daily Pricing Model Report: {date.today()}\n")
    
    report_lines.append("## 1. Performance Summary")
    report_lines.append(f"- **Transactions Validated**: {len(merged)}")
    report_lines.append(f"- **RMSE**: ${rmse:.2f}")
    report_lines.append(f"- **Bias**: ${bias:.2f} (Positive = Overestimating)")
    report_lines.append(f"- **MAPE**: {mape:.1f}%")
    report_lines.append(f"- **Hit Rate (<15% Error)**: {hit_rate:.1f}%\n")
    
    # Alerts
    report_lines.append("## 2. Refinement Suggestions")
    if bias > 5:
        report_lines.append("> [!WARNING] **High Positive Bias**: The model is consistently OVERESTIMATING prices. Consider increasing `SHOCK_DISCOUNT` or `STALENESS_DECAY`.")
    elif bias < -5:
        report_lines.append("> [!WARNING] **High Negative Bias**: The model is UNDERESTIMATING. Consider relaxing the auction exlusion or reducing Best Offer discount.")
    
    if mape > 20:
        report_lines.append("> [!CAUTION] **High Error Rate**: Average error is >20%. The model may be unstable.")
    else:
        report_lines.append("> [!TIP] **Model is Stable**: Error rates are within acceptable bounds.")
    
    report_lines.append("\n## 3. Top Outliers (Biggest Misses)")
    report_lines.append("| Date | Product ID | Actual | Predicted | Error % |")
    report_lines.append("|---|---|---|---|---|")
    
    outliers = merged.sort_values('abs_error', ascending=False).head(10)
    for _, row in outliers.iterrows():
        report_lines.append(f"| {row['date']} | {row['product_id']} | ${row['actual_price']:.2f} | ${row['predicted_price']:.2f} | {row['pct_error']:.1f}% |")
    
    # Save Report
    report_content = "\n".join(report_lines)
    
    # Save to local file
    output_path = "daily_model_report.md"
    with open(output_path, "w") as f:
        f.write(report_content)
        
    print(f"Report generated: {output_path}")
    print(report_content)
    
    # 5. Save to Database
    print("Saving metrics to database...")
    try:
        cur = conn.cursor()
        
        # A. Aggregate Stats
        # Default model version if not in df? df_est has it.
        # Assuming single model version for now or taking majority.
        model_ver = df_est['model_version'].iloc[0] if 'model_version' in df_est else 'v1_unknown'
        
        insert_perf_sql = """
            INSERT INTO daily_model_performance (
                date, model_version, rmse, mae, bias, mape, sentinel_count, hit_rate
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date, model_version) DO UPDATE SET
                rmse = EXCLUDED.rmse,
                mae = EXCLUDED.mae,
                bias = EXCLUDED.bias,
                mape = EXCLUDED.mape,
                sentinel_count = EXCLUDED.sentinel_count,
                hit_rate = EXCLUDED.hit_rate
        """
        cur.execute(insert_perf_sql, (
            date.today(), model_ver, 
            float(rmse), float(mae), float(bias), float(mape), 
            int(len(merged)), float(hit_rate)
        ))
        
        # B. Per-Card Updates
        # Update price_history with actual_sold_price and error
        # We need to update specific rows identified by (product_id, date)
        # Using executemany for efficiency
        
        update_data = []
        for _, row in merged.iterrows():
            update_data.append((
                row['actual_price'], 
                row['pct_error'], 
                row['product_id'], 
                row['date']
            ))
            
        update_hist_sql = """
            UPDATE price_history 
            SET actual_sold_price = %s, error_pct = %s
            WHERE product_id = %s AND date = %s
        """
        cur.executemany(update_hist_sql, update_data)
        
        conn.commit()
        print("Database stats updated successfully.")
        cur.close()
        
    except Exception as e:
        conn.rollback()
        print(f"Error saving to DB: {e}")

    conn.close()


    conn.close()

if __name__ == "__main__":
    validate_model()
