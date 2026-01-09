
from database import get_db_connection

def show_full_premium():
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = """
    SELECT DISTINCT ON (c.product_id)
        c.year,
        c.set_name,
        c.player_name,
        c.card_number,
        c.parallel_type,
        c.grader, 
        c.grade, 
        ph.estimated_market_value, 
        ph.driving_factor
    FROM price_history ph
    JOIN cards c ON ph.product_id = c.product_id
    WHERE ph.date = (SELECT MAX(date) FROM price_history)
    AND ph.estimated_market_value > 20
    ORDER BY c.product_id, ph.estimated_market_value DESC
    LIMIT 15;
    """
    
    try:
        cur.execute(query)
        rows = cur.fetchall()
        print("| Year | Set | Player | Card # | Parallel | Grader | Grade | Est. Value | Factor |")
        print("|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            year = r[0] or '-'
            set_name = r[1] or '-'
            player = r[2] or '-'
            card_num = r[3] or '-'
            parallel = r[4] or 'Base'
            grader = r[5] or '-'
            grade = r[6] or '-'
            value = r[7]
            factor = r[8] or '-'
            print(f"| {year} | {set_name} | {player} | {card_num} | {parallel} | {grader} | {grade} | ${value:.2f} | {factor} |")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    show_full_premium()
