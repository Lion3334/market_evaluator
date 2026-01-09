from database import get_db_connection
import traceback

def analyze_player(player_name):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print(f"--- Market Analysis: {player_name} ---\n")
        
        # 1. Total Active (Clean)
        cur.execute("""
            SELECT COUNT(*) FROM active_listings 
            WHERE title ILIKE %s AND is_ignored = FALSE
        """, (f'%{player_name}%',))
        total = cur.fetchone()[0]
        print(f"Total Active Listings (Filtered): {total}")
        
        # 2. Buying Options Breakdown
        print("\nBuying Formats:")
        cur.execute("""
            SELECT 
                CASE 
                    WHEN buying_options LIKE '%%AUCTION%%' THEN 'Auction'
                    ELSE 'Buy It Now'
                END,
                COUNT(*),
                AVG(price)
            FROM active_listings
            WHERE title ILIKE %s AND is_ignored = FALSE
            GROUP BY 1
        """, (f'%{player_name}%',))
        
        rows = cur.fetchall()
        for row in rows:
            if len(row) < 3:
                print(f"Skipping malformed row: {row}")
                continue
            fmt, count, avg_price = row
            avg_val = float(avg_price) if avg_price else 0.0
            print(f"  {fmt}: {count} listings, Avg Price: ${avg_val:.2f}")

        # 3. Graded Breakdown
        print("\nGrade Distribution:")
        cur.execute("""
            SELECT grader, grade, COUNT(*), AVG(price)
            FROM active_listings
            WHERE title ILIKE %s AND is_ignored = FALSE
            GROUP BY grader, grade
            ORDER BY COUNT(*) DESC
        """, (f'%{player_name}%',))
        
        for row in cur.fetchall():
            grader, grade, count, avg = row
            print(f"  {grader} {grade}: {count} items (Avg: ${float(avg):.2f})")

        conn.close()

    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    player = "Sam LaPorta"
    if len(sys.argv) > 1:
        player = sys.argv[1]
    analyze_player(player)
