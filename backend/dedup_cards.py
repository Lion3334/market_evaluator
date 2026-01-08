import psycopg2

DB_NAME = "cardpulse"

def deduplicate():
    conn = psycopg2.connect(database=DB_NAME)
    cur = conn.cursor()
    
    print("Analyzing duplicates...")
    
    # Find groups of cards that are chemically identical (Player, Year, Set, Number)
    # We prioritize keeping the one with a valid EPID
    
    cur.execute("""
        SELECT player_name, year, set_name, card_number, count(*), array_agg(product_id), array_agg(epid)
        FROM cards
        GROUP BY player_name, year, set_name, card_number
        HAVING count(*) > 1;
    """)
    
    duplicates = cur.fetchall()
    print(f"Found {len(duplicates)} groups of duplicates.")
    
    deleted_count = 0
    
    for group in duplicates:
        ids = group[5]
        epids = group[6]
        
        # Determine "winner"
        # Preference: Has specific EPID > Has 'none' > Has NULL
        # If multiple valid EPIDs, might be tricky, but usually one is just 'none'
        
        candidates = []
        for i, pid in enumerate(ids):
            ep = str(epids[i]) if epids[i] else "none"
            score = 0
            if ep.lower() not in ['none', 'missing', 'null']:
                score = 2
            elif ep.lower() == 'none':
                score = 1
            candidates.append((score, pid, ep))
            
        # Sort by score desc, then pid asc
        candidates.sort(key=lambda x: (x[0], -x[1]), reverse=True)
        winner = candidates[0]
        losers = candidates[1:]
        
        print(f"Group: {group[0]} #{group[3]}")
        print(f"  winner: {winner[1]} (EPID: {winner[2]})")
        
        for loss in losers:
            print(f"  deleting: {loss[1]} (EPID: {loss[2]})")
            # Re-link child records specifically?
            # CASCADE delete handles this if configured, but let's be safe and update references (if any exist) to winner
            # sales, forecasts, etc.
            
            cur.execute("UPDATE sales SET product_id = %s WHERE product_id = %s", (winner[1], loss[1]))
            cur.execute("UPDATE forecasts SET product_id = %s WHERE product_id = %s", (winner[1], loss[1]))
            
            # Now delete the card
            cur.execute("DELETE FROM cards WHERE product_id = %s", (loss[1],))
            deleted_count += 1
            
    conn.commit()
    conn.close()
    print(f"Cleanup complete. Deleted {deleted_count} duplicate cards.")

if __name__ == "__main__":
    deduplicate()
