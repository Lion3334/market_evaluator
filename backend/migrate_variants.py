import psycopg2
import sys

# Connect to database
try:
    conn = psycopg2.connect(database="cardpulse")
    cur = conn.cursor()
    print("Connected to database.")
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

def migrate():
    try:
        # 1. Add Columns to Cards Table
        print("1. Adding columns to cards table...")
        # Check if columns exist first
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='cards' AND column_name='grader';")
        if not cur.fetchone():
            cur.execute("ALTER TABLE cards ADD COLUMN grader VARCHAR(50) DEFAULT 'Raw';")
            cur.execute("ALTER TABLE cards ADD COLUMN grade VARCHAR(20) DEFAULT 'Raw';")
        
        # 2. Update Existing Rows to correspond to 'Raw' explicitly (if defaults didn't catch specific cases, but DEFAULT 'Raw' handles it)
        print("2. Ensuring existing rows are marked as Raw/Raw...")
        cur.execute("UPDATE cards SET grader = 'Raw', grade = 'Raw' WHERE grader IS NULL;")
        
        # 3. Modify Unique Constraint
        # We need to find the name of the existing unique constraint first
        print("3. Updating Unique Constraint...")
        cur.execute("""
            SELECT conname
            FROM pg_constraint
            WHERE conrelid = 'cards'::regclass AND contype = 'u';
        """)
        constraints = cur.fetchall()
        for c in constraints:
            # We assume the complex one is the target. Let's drop all unique constraints on cards to be safe and recreate the big one
            # Or simpler: just try to drop the one we know exists if named, or drop by definition
            print(f"   Dropping constraint: {c[0]}")
            cur.execute(f"ALTER TABLE cards DROP CONSTRAINT {c[0]};")
            
        # Add new constraint including grade/grader
        cur.execute("""
            ALTER TABLE cards ADD CONSTRAINT cards_unique_variant 
            UNIQUE(player_name, year, set_name, card_number, subset_insert, parallel_type, variation_type, grader, grade);
        """)

        # 4. Explode Variants
        print("4. Generating Variants (PSA 10, PSA 9, PSA <9)...")
        
        # Select all current "Raw" cards (which is all of them at this point)
        cur.execute("SELECT * FROM cards WHERE grader='Raw' AND grade='Raw';")
        # We need column names to construct insert safely or just select specific columns
        # Let's get list of columns first to be dynamic and safe
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'cards' AND column_name NOT IN ('product_id', 'created_at');")
        cols = [row[0] for row in cur.fetchall()]
        col_str = ", ".join(cols)
        
        # We will use INSERT INTO ... SELECT structure for efficiency
        
        variants = [
            ('PSA', '10'),
            ('PSA', '9'),
            ('PSA', '<9') # Grouped bucket
        ]
        
        for grader, grade in variants:
            print(f"   Creating variants for {grader} {grade}...")
            # We select all attributes from existing raw cards, but substitute grader/grade
            # We rely on Postgres param substitution or string formatting carefully
            # Since we are setting *literals* for grader/grade, we can just hardcode them in the SELECT list
            
            # Construct the SELECT part replacing 'grader' and 'grade' columns with new values
            select_parts = []
            for col in cols:
                if col == 'grader':
                    select_parts.append(f"'{grader}'")
                elif col == 'grade':
                    select_parts.append(f"'{grade}'")
                else:
                    select_parts.append(col)
            
            select_query = f"SELECT {', '.join(select_parts)} FROM cards WHERE grader='Raw' AND grade='Raw'"
            
            insert_query = f"""
                INSERT INTO cards ({col_str})
                {select_query}
                ON CONFLICT DO NOTHING;
            """
            cur.execute(insert_query)
            
        # 5. Clean Forecasts Table
        # Drop grade/grader columns from forecasts as they are now redundant with product_id
        print("5. Cleaning Forecasts table schema...")
        cur.execute("ALTER TABLE forecasts DROP COLUMN IF EXISTS grader;")
        cur.execute("ALTER TABLE forecasts DROP COLUMN IF EXISTS grade;")

        conn.commit()
        print("Migration Metadata Update Complete. Committing...")
        
        # 6. Verify count
        cur.execute("SELECT count(*) FROM cards;")
        final_count = cur.fetchone()[0]
        print(f"Final Card Count: {final_count}")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
