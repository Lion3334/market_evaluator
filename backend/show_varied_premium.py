
from database import get_db_connection

def show_varied_premium():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get a mix of high and mid-range premium cards
    query = """
    (SELECT DISTINCT ON (c.player_name, c.grader, c.grade)
        c.player_name, c.grader, c.grade, ph.estimated_market_value, ph.driving_factor
    FROM price_history ph
    JOIN cards c ON ph.product_id = c.product_id
    WHERE ph.date = (SELECT MAX(date) FROM price_history)
    AND ph.estimated_market_value > 20
    AND ph.estimated_market_value < 500
    LIMIT 5)
    UNION ALL
    (SELECT DISTINCT ON (c.player_name, c.grader, c.grade)
        c.player_name, c.grader, c.grade, ph.estimated_market_value, ph.driving_factor
    FROM price_history ph
    JOIN cards c ON ph.product_id = c.product_id
    WHERE ph.date = (SELECT MAX(date) FROM price_history)
    AND ph.estimated_market_value >= 500
    LIMIT 5);
    """
    
    try:
        cur.execute(query)
        rows = cur.fetchall()
        print("| Player | Grader | Grade | Est. Value | Driving Factor |")
        print("|---|---|---|---|---|")
        for r in rows:
            print(f"| {r[0]} | {r[1]} | {r[2]} | ${r[3]:.2f} | {r[4]} |")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    show_varied_premium()
