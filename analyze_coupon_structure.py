
import sqlite3
import pandas as pd
import json

DB_NAME = "tjk_races.db"

def analyze_structure():
    conn = sqlite3.connect(DB_NAME)
    
    # Parse daily_forecasts.sql
    coupons = []
    try:
        with open('daily_forecasts.sql', 'r') as f:
            for line in f:
                if "VALUES" in line:
                    # Extract city and legs JSON
                    # Format: ... VALUES ('date', 'City', ..., 'JSON')
                    parts = line.split("'")
                    city = parts[3]
                    legs_json = parts[-2]
                    coupons.append({'city': city, 'legs': legs_json})
    except:
        print("Could not read daily_forecasts.sql")
        return
        
    df_coupons = pd.DataFrame(coupons)
    
    for _, row in df_coupons.iterrows():
        print(f"\n🏙️  ANALYSIS: {row['city']}")
        legs = json.loads(row['legs'])
        
        for leg in legs:
            lid = leg['leg_no']
            sel_count = len(leg['horses'])
            sel_names = [h['horse_name'] for h in leg['horses']]
            
            # Find Race Info (Field Size)
            # We need to match leg_no to race_no. Usually Leg 1 is Race X.
            # We can't easily query race_no from here without the mapping, 
            # but we can try to find these horses in program_entries for that date/city to count field size.
            
            ph = ','.join([f"'{n}'" for n in sel_names])
            q = f"""
            SELECT pr.race_no, COUNT(*) as field_size 
            FROM program_entries pe 
            JOIN program_races pr ON pe.program_race_id = pr.id 
            WHERE pr.city LIKE '{row['city']}%' AND pr.date='19/01/2026'
            AND pr.race_no IN (SELECT race_no FROM program_entries pe2 JOIN program_races pr2 ON pe2.program_race_id=pr2.id WHERE pe2.horse_name IN ({ph}) AND pr2.date='19/01/2026')
            GROUP BY pr.race_no
            """
            
            try:
                res = pd.read_sql_query(q, conn)
                if not res.empty:
                    field_size = res.iloc[0]['field_size']
                    race_no = res.iloc[0]['race_no']
                    ratio = sel_count / field_size
                    print(f"  Leg {lid} (Race {race_no}): Field {field_size} -> Selected {sel_count} ({ratio:.0%})")
                    if ratio > 0.6: print(f"    ⚠️ OVER-COVERAGE: Covered >60% of field!")
                    if field_size > 12 and sel_count < 3: print(f"    ⚠️ RISKY: Large field ({field_size}) but only {sel_count} horses!")
            except:
                print(f"  Leg {lid}: Could not determine field size.")

if __name__ == "__main__":
    analyze_structure()
