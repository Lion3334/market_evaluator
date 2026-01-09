from database import get_db_connection

def analyze_listings():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print("--- Active Listings Analysis ---\n")

        # 1. Auctions vs BIN
        cur.execute("""
            SELECT buying_options, COUNT(*) 
            FROM active_listings 
            GROUP BY buying_options;
        """)
        print("Buying Options Breakdown:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]}")
            
        # 2. Average BIN Price
        # We look for rows that specificially have FIXED_PRICE in the string
        cur.execute("""
            SELECT AVG(price), MIN(price), MAX(price)
            FROM active_listings 
            WHERE buying_options LIKE '%FIXED_PRICE%';
        """)
        avg, min_p, max_p = cur.fetchone()
        if avg:
            print(f"\nBIN (Fixed Price) Stats:")
            print(f"  Average: ${float(avg):.2f}")
            print(f"  Range: ${float(min_p):.2f} - ${float(max_p):.2f}")
        else:
            print("\nNo BIN listings found.")

        # 3. Graded Cards Check (New Schema)
        print("\nGraded Card Distribution (Parsed):")
        cur.execute("SELECT grader, grade, COUNT(*) FROM active_listings GROUP BY grader, grade ORDER BY COUNT(*) DESC")
        for row in cur.fetchall():
            print(f"  {row[0]} {row[1]}: {row[2]}")

        # 4. Outlier & Ignore Stats
        print("\nQuality Filters:")
        cur.execute("SELECT COUNT(*) FROM active_listings WHERE is_ignored = TRUE")
        ignored = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM active_listings")
        total = cur.fetchone()[0]
        print(f"  Ignored (Outliers/Keywords): {ignored} / {total} ({(ignored/total)*100:.1f}%)")
        
        # 5. Variant Mapping
        cur.execute("SELECT COUNT(*) FROM active_listings WHERE product_id IS NOT NULL")
        mapped = cur.fetchone()[0]
        print(f"  Mapped to Internal Variant: {mapped} / {total} ({(mapped/total)*100:.1f}%)")

        print("\n--- Sample PSA 10 Titles (Mapped) ---")
        cur.execute("SELECT title, price FROM active_listings WHERE grade='10' AND grader='PSA' LIMIT 5")
        for t, p in cur.fetchall():
            print(f"  ${p}: {t}")

        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_listings()
