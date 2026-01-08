#!/usr/bin/env python3
"""Generate synthetic transaction data for ML development."""

import psycopg2
import random
from datetime import datetime, timedelta

# Pilot cards to seed
PILOT_CARDS = [
    {"epid": "23084914150", "player": "Drake Maye", "year": 2024, "set": "Donruss Optic", "variant": "Rookie Kings"},
    {"epid": "23084900001", "player": "Caleb Williams", "year": 2024, "set": "Topps Chrome", "variant": "Cosmic"},
    {"epid": "23084900002", "player": "Jayden Daniels", "year": 2024, "set": "Prizm", "variant": "Base RC"},
    {"epid": "23084900003", "player": "Marvin Harrison Jr", "year": 2024, "set": "Prizm", "variant": "Silver"},
    {"epid": "23084900004", "player": "Brock Bowers", "year": 2024, "set": "Donruss", "variant": "Rated Rookie"},
]

GRADES = ["RAW", "PSA_9", "PSA_10"]
GRADE_MULTIPLIERS = {"RAW": 1.0, "PSA_9": 1.5, "PSA_10": 2.5}

def generate_transactions(epid, base_price, days_back=90, avg_sales_per_week=3):
    """Generate realistic transactions with trend and noise."""
    transactions = []
    start_date = datetime.now() - timedelta(days=days_back)
    
    # Random trend: -10% to +20% over period
    trend = random.uniform(-0.1, 0.2)
    daily_trend = trend / days_back
    
    for day in range(days_back):
        current_date = start_date + timedelta(days=day)
        # Poisson-ish distribution for sales per day
        sales_today = random.randint(0, 2) if random.random() < (avg_sales_per_week / 7) else 0
        
        for _ in range(sales_today):
            grade = random.choices(GRADES, weights=[50, 30, 20])[0]
            multiplier = GRADE_MULTIPLIERS[grade]
            
            # Price with trend + noise
            trend_adj = 1 + (daily_trend * day)
            noise = random.uniform(0.85, 1.15)
            price = round(base_price * multiplier * trend_adj * noise, 2)
            
            transactions.append({
                "epid": epid,
                "date": current_date.date(),
                "price": price,
                "grade": grade,
                "title": f"Synthetic Transaction for EPID {epid}"
            })
    
    return transactions

def populate_db():
    conn = psycopg2.connect(database="cardpulse")
    cur = conn.cursor()
    
    # Clear existing synthetic data
    cur.execute("DELETE FROM transactions WHERE source = 'Synthetic'")
    
    total = 0
    for card in PILOT_CARDS:
        # Insert card if not exists
        cur.execute("""
            INSERT INTO cards (epid, player_name, year, set_name, variant)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (epid) DO NOTHING
        """, (card["epid"], card["player"], card["year"], card["set"], card["variant"]))
        
        # Generate transactions
        base_price = random.uniform(100, 500)  # Random base for variety
        txns = generate_transactions(card["epid"], base_price)
        
        for t in txns:
            cur.execute("""
                INSERT INTO transactions (card_epid, txn_date, price, grade, source, title)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (t["epid"], t["date"], t["price"], t["grade"], "Synthetic", t["title"]))
        
        total += len(txns)
        print(f"  {card['player']} - {card['variant']}: {len(txns)} transactions")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"\nTotal synthetic transactions added: {total}")

if __name__ == "__main__":
    print("Generating synthetic transaction data...")
    populate_db()
