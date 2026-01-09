import pandas as pd
import matplotlib.pyplot as plt
from database import get_db_connection
import sys

def analyze_supply():
    conn = get_db_connection()
    
    # query 1: All listings with start_date and price, filtered to BIN/Fixed Price
    # active_listings represent "Survivor" data, so historical "active" counts are estimates.
    query = """
    SELECT 
        item_id, 
        price, 
        start_date, 
        buying_options 
    FROM active_listings 
    WHERE (buying_options LIKE '%FIXED_PRICE%' OR buying_options LIKE '%BIN%')
    AND start_date IS NOT NULL
    MINUS
    SELECT item_id, price, start_date, buying_options FROM active_listings WHERE is_ignored = TRUE
    """
    
    # Postgres uses EXCEPT instead of MINUS usually, but standard SQL... let's stick to simpler WHERE
    query = """
    SELECT 
        item_id, 
        price, 
        start_date
    FROM active_listings 
    WHERE (buying_options LIKE '%FIXED_PRICE%' OR buying_options LIKE '%BIN%')
    AND start_date IS NOT NULL
    AND is_ignored = FALSE
    ORDER BY start_date ASC
    """
    
    print("Fetching data...")
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Convert dates
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['date'] = df['start_date'].dt.date
    
    print(f"Loaded {len(df)} BIN listings.")
    
    # 1. Daily New Listings
    daily_new = df.groupby('date').size()
    
    # 2. Daily Median Price (New Listings)
    daily_median_new = df.groupby('date')['price'].median()
    
    # 3. Daily Median Price (Active Listings)
    # This requires iterating through each day in the range
    date_range = pd.date_range(start=df['date'].min(), end=df['date'].max())
    
    active_medians = []
    active_counts = []
    
    print("Calculating daily active stats...")
    for d in date_range:
        day_date = d.date()
        # Active on day D means: start_date <= D 
        # (Assuming they haven't ended? We don't have historical end dates for ended items reliably in this table alone)
        # We will assume survivor bias: items in this table are "Currently Active". 
        # So if start_date <= D, it was active on D (and is still active today).
        # This underestimates historical supply (missing items that sold), but matches "active listings that we have".
        
        mask = (df['date'] <= day_date)
        active_subset = df[mask]
        
        if not active_subset.empty:
            active_medians.append(active_subset['price'].median())
            active_counts.append(len(active_subset))
        else:
            active_medians.append(0)
            active_counts.append(0)
            
    # Combine into DataFrame
    stats = pd.DataFrame({
        'date': date_range,
        'new_listings_count': daily_new.reindex(date_range, fill_value=0).values,
        'new_median_price': daily_median_new.reindex(date_range).values,
        'active_median_price_cuml': active_medians,
        'active_count_cuml': active_counts
    })
    
    stats.set_index('date', inplace=True)
    
    # Print Summary (Last 10 Days)
    print("\n--- Last 10 Days of Supply Data ---")
    print(stats.tail(10)[['new_listings_count', 'new_median_price', 'active_median_price_cuml']])

    # Filter for Visualization (Last 14 Days)
    cutoff_date = pd.Timestamp.now().floor('D') - pd.Timedelta(days=14)
    stats_plot = stats[stats.index >= cutoff_date]

    # Visualization
    try:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        
        # Plot 1: Volume with Dual Axis
        ax1.set_title('Daily Supply Volume (Last 14 Days)')
        
        # Primary Axis (Left): Total Active (Line)
        ax1.plot(stats_plot.index, stats_plot['active_count_cuml'], label='Total Active (Cumulative)', color='orange', linewidth=2, linestyle='--')
        ax1.set_ylabel('Total Active Count', color='orange')
        ax1.tick_params(axis='y', labelcolor='orange')
        ax1.grid(True, alpha=0.3)
        
        # Secondary Axis (Right): New BIN Listings (Bars)
        ax1_right = ax1.twinx()
        ax1_right.bar(stats_plot.index, stats_plot['new_listings_count'], label='New BIN Listings', color='skyblue', alpha=0.6, width=0.8)
        ax1_right.set_ylabel('New Daily Listings', color='skyblue')
        ax1_right.tick_params(axis='y', labelcolor='skyblue')
        
        # Combine legends
        lines, labels = ax1.get_legend_handles_labels()
        bars, bar_labels = ax1_right.get_legend_handles_labels()
        ax1.legend(lines + bars, labels + bar_labels, loc='upper left')
        
        # Plot 2: Price
        ax2.plot(stats_plot.index, stats_plot['new_median_price'], label='Median Price (New Only)', marker='.', linestyle='none', color='blue', alpha=0.5)
        ax2.plot(stats_plot.index, stats_plot['active_median_price_cuml'], label='Median Price (All Active)', color='red', linewidth=2)
        ax2.set_title('Median Price Trends (BIN)')
        ax2.set_ylabel('Price ($)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_file = 'supply_analysis_plot.png'
        plt.savefig(output_file)
        print(f"\nPlot saved to {output_file}")
    except Exception as e:
        print(f"Could not generate plot: {e}")

if __name__ == "__main__":
    analyze_supply()
