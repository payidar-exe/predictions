
import sqlite3
import pandas as pd
import numpy as np
import joblib
import json
import math
import sys
import os
import argparse
from datetime import datetime

# Import logical components
sys.path.append(os.getcwd())
from production_engine import (
    get_historical_stats_v10,
    compute_galop_features,
    optimize_coupon_logic,
    golden_ratio_score, fibonacci_resonance, prime_harmony,
    cosmic_wave, chaos_attractor, numerology_score, moon_phase,
    PHI, FIBONACCI
)

DB_NAME = "tjk_races.db"

def generate_and_push_forecasts(target_date, all_cities=False):
    print(f"\n🔮 KAHIN v10: Generating Forecasts for {target_date}")
    print("=" * 70)
    
    # Load Models (Using Honest Models for consistency with recent validation)
    try:
        lgbm = joblib.load('model_honest_lgbm.pkl')
        cat = joblib.load('model_honest_cat.pkl')
        xgb_model = joblib.load('model_honest_xgb.pkl')
        le_track = joblib.load('le_track_honest.pkl')
        le_city = joblib.load('le_city_honest.pkl')
        print("✅ Models loaded successfully.")
    except:
        print("❌ Model load failed! Cannot predict.")
        return

    # Fetch Program
    conn = sqlite3.connect(DB_NAME)
    
    # Check `program_races` table first (Scraped future races go there?)
    # scrape_program.py inserts into `program_races` and `program_entries`.
    
    pr_df = pd.read_sql_query(f"SELECT * FROM program_races WHERE date='{target_date}'", conn)
    
    if pr_df.empty:
        print(f"❌ No program found for {target_date} in `program_races`. Did scraper run?")
        return
        
    cities = pr_df['city'].unique()
    
    # Filter for Turkish Cities
    tr_city_names = ['İstanbul', 'Ankara', 'İzmir', 'Adana', 'Bursa', 'Kocaeli', 'Şanlıurfa', 'Diyarbakır', 'Antalya', 'Elazığ']
    
    if all_cities:
        # Process ALL Turkish cities found in program
        filtered_cities = [c for c in cities if any(tr_c in c for tr_c in tr_city_names)]
        print(f"🌍 All-Cities Mode: Processing {len(filtered_cities)} TR cities")
    else:
        # Manual selection (legacy behavior)
        filtered_cities = []
        for c in cities:
            if any(tr_c in c for tr_c in tr_city_names):
                filtered_cities.append(c)
            
    print(f"🌍 Available Cities: {list(cities)}")
    print(f"🇹🇷 Selected TR Cities: {filtered_cities}")
    
    sql_statements = []
    
    for city in filtered_cities:
        # Load Entries
        city_races = pr_df[pr_df['city'] == city]
        race_ids = tuple(city_races['id'].tolist())
        
        if not race_ids: continue
        
        placeholders = ','.join(['?'] * len(race_ids))
        entries_query = f"""
            SELECT 
                pe.*, pr.race_no, pr.date, pr.city, pr.distance, pr.track_type, pr.race_type, pr.time
            FROM program_entries pe
            JOIN program_races pr ON pe.program_race_id = pr.id
            WHERE pr.id IN ({placeholders})
        """
        df = pd.read_sql_query(entries_query, conn, params=race_ids)
        
        # Deduplicate: Ensure same horse doesn't appear twice in the same race (DB integrity)
        df = df.drop_duplicates(subset=['race_no', 'horse_name'])
        
        # Galop Data
        horse_names = tuple(df['horse_name'].dropna().unique().tolist())
        if horse_names:
            ph2 = ','.join(['?'] * len(horse_names))
            g_df = pd.read_sql_query(f"SELECT * FROM gallops WHERE horse_name IN ({ph2})", conn, params=horse_names)
        else: g_df = pd.DataFrame()
        
        # --- PREDICT ---
        # Normalize columns for prediction function
        # production_engine uses 'hp', 'weight', 'track_type' etc.
        # program_entries has similar cols.
        
        # Encode
        def safe_enc(le, val):
            try: return le.transform([str(val)])[0]
            except: return 0
            
        df['track_encoded'] = df['track_type'].apply(lambda x: safe_enc(le_track, x))
        df['city_encoded'] = df['city'].apply(lambda x: safe_enc(le_city, x))
        
        # Historicals (using results table for history)
        df_hist = df.copy() # We iterate this
        
        m5_v, imp_v, com_v, trk_v, own_v, trn_v = [], [], [], [], [], []
        q_vecs = {k:[] for k in ['gold','fib','pri','cos','chaos','num','moon']}
        
        # Using shared connection for history lookup (from `results` table)
        # Note: `get_historical_stats_v10` queries `results` table.
        
        for idx, row in df.iterrows():
            m5, imp, com, trk, own, trn = get_historical_stats_v10(
                row['horse_name'], row['jockey'], row['track_type'], 
                row.get('trainer'), row.get('owner'), target_date, conn=conn
            )
            m5_v.append(m5); imp_v.append(imp); com_v.append(com)
            trk_v.append(trk); own_v.append(own); trn_v.append(trn)
            
             # Quantum
            rn = row['race_no'] or 1
            hn = row['horse_name'] or "X"
            q_vecs['gold'].append(golden_ratio_score(m5))
            q_vecs['fib'].append(fibonacci_resonance(rn, ord(hn[0])%10))
            q_vecs['pri'].append(prime_harmony(float(row['hp'] or 0), float(row['weight'] or 55)))
            q_vecs['cos'].append(cosmic_wave(target_date, rn))
            q_vecs['chaos'].append(chaos_attractor(m5, com, trk))
            q_vecs['num'].append(numerology_score(hn))
            q_vecs['moon'].append(moon_phase(target_date))

        df['momentum_5'] = m5_v
        df['improvement_trend'] = imp_v
        df['combo_win_rate'] = com_v
        df['track_win_rate'] = trk_v
        df['owner_win_rate'] = own_v
        df['trainer_win_rate_ext'] = 0.1 # Placeholder if unknown
        df['trainer_recent_form'] = trn_v
        
        for k in q_vecs: df[f'quantum_{"golden" if k=="gold" else "fibonacci" if k=="fib" else "prime" if k=="pri" else "cosmic" if k=="cos" else "chaos" if k=="chaos" else "numerology" if k=="num" else "moon"}'] = q_vecs[k]
        
        df['quantum_field'] = (df['quantum_golden']*PHI + df['quantum_fibonacci']*(FIBONACCI[7]/21) + df['quantum_prime']*math.pi + df['quantum_cosmic']*math.e + df['quantum_chaos']*2.718 + df['quantum_numerology']*7/9 + df['quantum_moon']*0.5)/10
        
        # Galop Integration
        df = compute_galop_features(df, g_df, target_date)
        
        features = ['distance', 'weight', 'track_encoded', 'city_encoded', 'hp',
            'momentum_5', 'improvement_trend', 'owner_win_rate', 'trainer_win_rate_ext', 'trainer_recent_form',
            'combo_win_rate', 'track_win_rate',
            'quantum_golden', 'quantum_fibonacci', 'quantum_prime', 'quantum_cosmic', 'quantum_chaos', 'quantum_numerology', 'quantum_moon', 'quantum_field',
            'days_since_galop', 'galop_speed']
            
        for f in features: 
            if f not in df.columns: df[f] = 0
            df[f] = pd.to_numeric(df[f], errors='coerce').fillna(0)
            
        # Filter Out "UNKNOWN" or Specific Horses (User Request)
        df['horse_name'] = df['horse_name'].str.strip()
        df = df[~df['horse_name'].str.contains('UNKNOWN', case=False, na=False)]
        df = df[~df['horse_name'].str.contains('VENTUS', case=False, na=False)] # Extra safety

        # Ensure race_no is int
        df['race_no'] = pd.to_numeric(df['race_no'], errors='coerce')
        
        # ... (Prediction Logic) ...
        
        X = df[features].astype(float)
        p = (lgbm.predict_proba(X)[:,1] + cat.predict_proba(X)[:,1] + xgb_model.predict_proba(X)[:,1]) / 3
        df['score'] = (p + (df['galop_score']-0.5)*0.2).clip(0,1)

        # --- QUANTUM & SURPRISE BOOST (Aggressive - Best Tested) ---
        # 1. Chaos Boost
        mask_chaos = (df['score'] < 0.25) & (df['quantum_chaos'] > 0.70)
        df.loc[mask_chaos, 'score'] += (df.loc[mask_chaos, 'quantum_chaos'] * 0.45)
        
        # 2. Galop Boost
        mask_galop = (df['momentum_5'] < 0.55) & (df['galop_score'] > 0.70)
        df.loc[mask_galop, 'score'] += 0.35
        
        # 3. Jockey Factor
        mask_joc = (df['combo_win_rate'] > 0.20) & (df['score'] < 0.25)
        df.loc[mask_joc, 'score'] += 0.25
        
        # Re-clip
        df['score'] = df['score'].clip(0, 0.98) # Cap slightly below 1
        
        # --- COUPON GENERATION ---
        race_nos = sorted(df['race_no'].unique())
        
        if len(race_nos) < 6:
            print(f"Skipping {city}: Only {len(race_nos)} races found (Need 6+ for Altılı).")
            continue
            
        legs = race_nos[-6:]
        legs_data = []
        for r in legs:
            entries = df[df['race_no'] == r].sort_values('score', ascending=False)
            legs_data.append([(x['horse_name'], x['score']) for _, x in entries.iterrows()])
            
        selection, cost = optimize_coupon_logic(legs_data, 700.0)
        
        # Format for SQL
        legs_json = []
        
        def generate_ai_comment(row):
            """Generate rule-based AI comment"""
            comments = []
            
            # Surprise Signals
            if row['quantum_chaos'] > 0.8 and row['score'] > 0.3: comments.append("Kuantum formülüyle sürpriz yapabilir!")
            elif row['momentum_5'] < 0.4 and row['galop_score'] > 0.7: comments.append("Gizli formda, hazırlıkları harika.")
            
            # Form
            if row['momentum_5'] > 0.7: comments.append("Form durumu zirvede.")
            elif row['momentum_5'] > 0.5: comments.append("Formunu koruyor.")
            
            # Galop
            if row['galop_score'] > 0.7: comments.append("İdman pistinde uçuyor!")
            elif row.get('days_since_galop', 999) < 4: comments.append("Nefesi açık.")
            
            # Stats
            if row['track_win_rate'] > 0.3: comments.append("Bu pisti sever.")
            if row['combo_win_rate'] > 0.2: comments.append("Jokeyiyle uyumlu.")
            
            # Legacy/Quantum
            if row['quantum_field'] > 0.8: comments.append("Kahin'in favorisi!")
            
            if not comments: 
                if row['score'] > 0.8: comments.append("Kazanmaya çok yakın.")
                else: comments.append("Sürpriz hanesinde.")
                
            return " ".join(comments[:2])

        for i, leg_sel in enumerate(selection):
            leg_horses_json = []
            race_num = legs[i]
            
            # Pre-filter DF for this race to avoid repeated lookups
            race_df = df[df['race_no'] == race_num]
            
            for h_tuple in leg_sel:
                h_name, h_score = h_tuple
                
                try:
                    # Robust Lookup
                    row_matches = race_df[race_df['horse_name'] == h_name]
                    if not row_matches.empty:
                        row = row_matches.iloc[0]
                        note = generate_ai_comment(row)
                        
                        leg_horses_json.append({
                            "horse_name": h_name,
                            "jockey": str(row['jockey'] or "Unknown"),
                            "trainer": str(row['trainer'] or "Unknown"),
                            "score": round(float(h_score), 2),
                            "ai_note": note,
                            "is_banko": (h_score > 0.85)
                        })
                    else:
                        raise Exception("Horse not found in DF")
                except Exception as e:
                    # Fallback
                    leg_horses_json.append({
                        "horse_name": h_name,
                        "jockey": "?", 
                        "score": round(float(h_score), 2),
                        "ai_note": "Veri hatası.",
                        "is_banko": False
                    })

            # Find Race Time
            r_time = "Unknown"
            if not race_df.empty:
                r_time = race_df.iloc[0]['time']
            
            legs_json.append({
                "leg_no": i+1,
                "leg_result": "pending",
                "horses": leg_horses_json,
                "actual_winner": None,
                "race_time": str(r_time)
            })
            
        # Add Race Times from program data
        # We can map race_no to time
        # df has 'race_no' and we need 'time' from program_races? 
        # df came from program_entries joined with program_races, so it has 'time' col (check query).
        # Query: SELECT pe.*, pr.race_no, pr.date, pr.city, pr.distance, pr.track_type, pr.race_type ...
        # Wait, query didn't select 'time'.
        
        # Let's verify columns in query:
        # SELECT pe.*, pr.race_no, pr.date, pr.city, pr.distance, pr.track_type, pr.race_type FROM ...
        # 'time' is in program_races. 
        # I should add 'pr.time' to query to be safe.
        

            
        # SQL Insert
        # Date format YYYY-MM-DD
        try:
            parts = target_date.split('/')
            sql_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
        except: sql_date = target_date # Assume iso
        
        # Use city name only (strip suffix like ' (8. Y.G.)') if desired, but keeping exact match is safer for now
        # or remove for cleaner UI.
        clean_city = city.split('(')[0].strip()
        
        title = f"{clean_city} Kahin Analizi"
        subtitle = f"TUTAR: {cost:.2f} TL"
        legs_str = json.dumps(legs_json, ensure_ascii=False).replace("'", "''")
        
        sql = f"""
        INSERT INTO coupons (date, city, type, star_cost, title, subtitle, status, winning_amount, legs)
        VALUES ('{sql_date}', '{city}', 'premium', 50, '{title}', '{subtitle}', 'pending', 0, '{legs_str}');
        """
        sql_statements.append(sql.strip())
        print(f"Designed Coupon for {city}: {cost} TL")

    conn.close()
    
    if sql_statements:
        with open('daily_forecasts.sql', 'w') as f:
            for s in sql_statements:
                f.write(s + "\n")
        print("\n✅ `daily_forecasts.sql` generated successfully!")
    else:
        print("\n⚠️ No coupons generated.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate horse racing forecasts')
    parser.add_argument('--date', type=str, default=None,
                        help='Target date in DD/MM/YYYY format (default: today)')
    parser.add_argument('--all-cities', action='store_true',
                        help='Process all Turkish cities automatically')
    
    args = parser.parse_args()
    
    # Determine target date
    if args.date:
        target_date = args.date
    else:
        target_date = datetime.now().strftime("%d/%m/%Y")
    
    print(f"📅 Target Date: {target_date}")
    print(f"🌍 All Cities Mode: {args.all_cities}")
    
    generate_and_push_forecasts(target_date, all_cities=args.all_cities)
