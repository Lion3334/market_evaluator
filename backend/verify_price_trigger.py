from database import get_db_connection
import time

def verify_trigger():
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("Verifying Price History Trigger...")

    # 1. Pick a victim (listing)
    cur.execute("SELECT item_id, price, title FROM active_listings LIMIT 1")
    row = cur.fetchone()
    if not row:
        print("[!] No active listings found to test.")
        return
    
    item_id, original_price, title = row
    test_price = float(original_price) + 1.00
    
    print(f"Target: {item_id} | {title[:30]}...")
    print(f"Original Price: {original_price} -> Changing to: {test_price}")
    
    # 2. Update Price
    cur.execute("UPDATE active_listings SET price = %s WHERE item_id = %s", (test_price, item_id))
    conn.commit()
    
    # 3. Check History Log
    time.sleep(1) # tiny wait just in case
    cur.execute("""
        SELECT old_price, new_price, change_date 
        FROM listing_price_changes 
        WHERE item_id = %s 
        ORDER BY change_date DESC LIMIT 1
    """, (item_id,))
    
    history = cur.fetchone()
    
    if history:
        old_p, new_p, date = history
        print(f"✅ Trigger SUCCESS! Logged change: {old_p} -> {new_p} at {date}")
    else:
        print("❌ Trigger FAILED! No history record found.")

    # 4. Cleanup (Revert Price)
    cur.execute("UPDATE active_listings SET price = %s WHERE item_id = %s", (original_price, item_id))
    conn.commit()
    print(f"Reverted price back to {original_price}")

    conn.close()

if __name__ == "__main__":
    verify_trigger()
