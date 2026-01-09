
from database import get_db_connection

def show_high_volume_estimates():
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = """
    SELECT 
        c.player_name, 
        c.grader, 
        c.grade, 
        ph.estimated_market_value, 
        ph.driving_factor,
        dsm.total_active_fixed_price_only as volume
    FROM price_history ph
    JOIN cards c ON ph.product_id = c.product_id
    JOIN daily_supply_metrics dsm ON ph.product_id = dsm.product_id AND ph.date = dsm.date
    WHERE ph.date = (SELECT MAX(date) FROM price_history)
    ORDER BY dsm.total_active_fixed_price_only DESC
    LIMIT 5;
    """
    
    try:
        cur.execute(query)
        rows = cur.fetchall()
        print("| Player | Grader | Grade | Est. Value | Driving Factor | Volume |")
        print("|---|---|---|---|---|---|")
        for r in rows:
            print(f"| {r[0]} | {r[1]} | {r[2]} | ${r[3]:.2f} | {r[4]} | {r[5]} |")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    show_high_volume_estimates()
