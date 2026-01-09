from database import get_db_connection

def seed_cards():
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("Seeding base cards...")
    
    # List of tuples: (player, year, set_name, subset, card_number, epid)
    # Re-using the list we built up in previous sessions
    base_cards = [
        ("Drake Maye", 2024, "Panini Donruss", "Downtown", "13", "147046281771"),
        ("Caleb Williams", 2024, "Panini Donruss", "Downtown", "1", None), 
        ("Jayden Daniels", 2024, "Panini Donruss", "Downtown", "2", None),
        ("Bo Nix", 2024, "Panini Donruss", "Downtown", "None", "235777309990"),
        ("Brock Bowers", 2024, "Panini Donruss", "Downtown", "None", "235777309990"), # Check EPID reuse? No, just placeholder
        ("Jordan Love", 2024, "Panini Donruss", "Downtown", "5", None),
        ("J.J. McCarthy", 2024, "Panini Donruss", "Downtown", "None", None),
        ("Michael Penix Jr.", 2024, "Panini Donruss", "Downtown", "None", None),
        ("Rome Odunze", 2024, "Panini Donruss", "Downtown", "None", None),
        ("Malik Nabers", 2024, "Panini Donruss", "Downtown", "None", None),
        ("Xavier Worthy", 2024, "Panini Donruss", "Downtown", "None", None),
        # ... and older ones
        ("Puka Nacua", 2024, "Panini Donruss", "Downtown", "None", None),
        ("Lamar Jackson", 2024, "Panini Donruss", "Downtown", "None", None),
        ("Josh Allen", 2024, "Panini Donruss", "Downtown", "None", None),
        ("Tyreek Hill", 2024, "Panini Donruss", "Downtown", "None", None),
        ("Travis Kelce", 2024, "Panini Donruss", "Downtown", "None", None),
        ("Brock Purdy", 2024, "Panini Donruss", "Downtown", "None", None),
        ("Sam LaPorta", 2024, "Panini Donruss", "Downtown", "None", None),
        ("Marvin Harrison Jr.", 2024, "Panini Donruss", "Downtown", "None", None),
        ("Terrell Owens", 2024, "Panini Donruss", "Downtown", "None", None)
    ]
    
    # Variants to explode
    variants = ["Raw", "10", "9", "<9"]
    graders = {
        "Raw": "Raw",
        "10": "PSA",
        "9": "PSA",
        "<9": "PSA"
    }

    inserted = 0
    for card in base_cards:
        player, year, set_name, subset, num, epid = card
        
        for v in variants:
            grader = graders[v]
            cur.execute("""
                INSERT INTO cards (player_name, year, set_name, subset_insert, card_number, epid, grader, grade)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (epid, player_name, year, set_name, subset_insert, card_number, grader, grade) 
                DO NOTHING;
            """, (player, year, set_name, subset, num, epid, grader, v))
            inserted += 1
            
    conn.commit()
    cur.close()
    conn.close()
    print(f"Seeding complete. Attempted insert of {inserted} variants.")

if __name__ == "__main__":
    seed_cards()
