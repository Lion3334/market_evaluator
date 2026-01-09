
from database import get_db_connection
import pandas as pd

def assign_sentinels():
    print("Assigning Sentinel cards (Value > $2, Distributed)...")
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Reset existing
        cur.execute("UPDATE cards SET is_sentinel = FALSE")
        
        # Fetch candidates: Active listings with recent supply metrics indicating price > $2
        query = """
            SELECT product_id, total_active_fixed_price_only, median_new_price
            FROM daily_supply_metrics
            WHERE median_new_price IS NOT NULL 
            AND median_new_price > 2.00
            AND total_active_fixed_price_only > 0
            ORDER BY median_new_price DESC
        """
        df = pd.read_sql(query, conn)
        
        if df.empty:
            print("No valid candidates found (check daily_supply_metrics).")
            return

        print(f"Found {len(df)} candidates > $2.")
        
        # Distribution Strategy: Stratified Sampling by Price
        # We want 100 cards. Let's take 25 from 4 quartiles to ensure coverage of cheap ($2-20), mid, and high end.
        
        sentinel_ids = []
        
        if len(df) < 100:
            sentinel_ids = df['product_id'].tolist()
        else:
            # Create 4 buckets based on Price
            df['quartile'] = pd.qcut(df['median_new_price'], 4, labels=False)
            
            for q in range(4):
                # In each quartile, pick top 25 by Volume (Liquidity is important for sentinels)
                bucket = df[df['quartile'] == q].sort_values('total_active_fixed_price_only', ascending=False)
                selected = bucket.head(25)
                sentinel_ids.extend(selected['product_id'].tolist())
                print(f"  Quartile {q}: Selected {len(selected)} (Price range: ${bucket['median_new_price'].min():.2f} - ${bucket['median_new_price'].max():.2f})")
        
        # Update DB
        if sentinel_ids:
            cur.execute("UPDATE cards SET is_sentinel = TRUE WHERE product_id = ANY(%s)", (sentinel_ids,))
            conn.commit()
            print(f"Successfully marked {len(sentinel_ids)} cards as Sentinels.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error assigning sentinels: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    assign_sentinels()
