"""
Assign Refresh Tiers to Cards

Tier definitions:
- Tier 1 (Daily): Est. Value > $50 OR Volume > 30
- Tier 2 (Every 2 days): Est. Value $10-$50 OR Volume 10-30
- Tier 3 (Every 4 days): Est. Value $2-$10 OR Volume 3-10
- Tier 4 (Weekly): Est. Value < $2 OR Volume < 3
"""

import pandas as pd
from datetime import date, timedelta
from database import get_db_connection

# Tier refresh intervals (days)
TIER_INTERVALS = {
    1: 1,   # Daily
    2: 2,   # Every 2 days
    3: 4,   # Every 4 days
    4: 7,   # Weekly
}

def assign_tiers():
    print("Assigning refresh tiers based on value and volume...")
    conn = get_db_connection()
    
    # Get latest estimates and supply metrics
    query = """
    SELECT DISTINCT ON (c.product_id)
        c.product_id,
        COALESCE(ph.estimated_market_value, 0) as est_value,
        COALESCE(dsm.total_active_fixed_price_only, 0) as volume
    FROM cards c
    LEFT JOIN price_history ph ON c.product_id = ph.product_id
        AND ph.date = (SELECT MAX(date) FROM price_history)
    LEFT JOIN daily_supply_metrics dsm ON c.product_id = dsm.product_id
        AND dsm.date = (SELECT MAX(date) FROM daily_supply_metrics)
    ORDER BY c.product_id
    """
    
    df = pd.read_sql(query, conn)
    print(f"Found {len(df)} cards to evaluate.")
    
    # Assign tiers
    def get_tier(row):
        if row['est_value'] > 50 or row['volume'] > 30:
            return 1
        elif row['est_value'] > 10 or row['volume'] > 10:
            return 2
        elif row['est_value'] > 2 or row['volume'] > 3:
            return 3
        else:
            return 4
    
    df['tier'] = df.apply(get_tier, axis=1)
    
    # Calculate next refresh due date
    today = date.today()
    df['next_refresh'] = df['tier'].apply(lambda t: today + timedelta(days=TIER_INTERVALS[t]))
    
    # Update database
    cur = conn.cursor()
    update_sql = """
        UPDATE cards 
        SET refresh_tier = %s, next_refresh_due = %s
        WHERE product_id = %s
    """
    
    updates = [(int(row['tier']), row['next_refresh'], int(row['product_id'])) 
               for _, row in df.iterrows()]
    
    cur.executemany(update_sql, updates)
    conn.commit()
    
    # Print summary
    tier_counts = df['tier'].value_counts().sort_index()
    print("\nTier Distribution:")
    for tier, count in tier_counts.items():
        interval = TIER_INTERVALS[tier]
        print(f"  Tier {tier} ({interval}d refresh): {count} cards")
    
    print(f"\nUpdated {len(updates)} cards with tier assignments.")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    assign_tiers()
