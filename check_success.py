
import sqlite3
import pandas as pd
import joblib
import sys
import os
import math

# Import components
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
TARGET_DATE = "16/01/2026"
CITIES = ['İzmir', 'Antalya']

def check_success():
    print(f"📊 CHECKING SUCCESS FOR {TARGET_DATE}")
    print("="*60)
    
    # Load Models
    try:
        lgbm = joblib.load('model_honest_lgbm.pkl')
        cat = joblib.load('model_honest_cat.pkl')
        xgb_model = joblib.load('model_honest_xgb.pkl')
        le_track = joblib.load('le_track_honest.pkl')
        le_city = joblib.load('le_city_honest.pkl')
    except:
        print("❌ Model load failed.")
        return

    conn = sqlite3.connect(DB_NAME)
    
    for city_key in CITIES:
        print(f"\n🏙️  {city_key.upper()}")
        print("-" * 50)
        
        # Get Races & Results
        # Note: program_races has 'city' like 'İzmir (8. Y.G.)'
        query = f"""
            SELECT r.id, r.race_no, r.city, res.horse_name as winner_name, res.ganyan
            FROM races r
            LEFT JOIN results res ON r.id = res.race_id
            WHERE r.date = '{TARGET_DATE}' AND r.city LIKE '%{city_key}%' AND res.rank = 1
            ORDER BY r.race_no
        """
        results_df = pd.read_sql_query(query, conn)
        
        if results_df.empty:
            print("⚠️ No results found.")
            # Try date format variance? Scraper uses DD/MM/YYYY usually.
            # Table usually stores as is.
            # Check program_races vs races? Scraping results into 'races' and 'results' tables.
            pass
            
        # Get Program Entries for Prediction
        # Need to find program races first to get the correct IDs
        pr_query = f"""
            SELECT id, city, race_no, time 
            FROM program_races 
            WHERE date='{TARGET_DATE}' AND city LIKE '%{city_key}%'
        """
        pr_df = pd.read_sql_query(pr_query, conn)
        race_ids = tuple(pr_df['id'].tolist())
        
        if not race_ids:
            print("❌ No program data.")
            continue
            
        placeholders = ','.join(['?'] * len(race_ids))
        entries_query = f"""
            SELECT pe.*, pr.race_no, pr.date, pr.city, pr.distance, pr.track_type
            FROM program_entries pe
            JOIN program_races pr ON pe.program_race_id = pr.id
            WHERE pr.id IN ({placeholders})
        """
        df = pd.read_sql_query(entries_query, conn, params=race_ids)
        
        # Galop load
        horse_names = tuple(df['horse_name'].dropna().unique().tolist())
        g_df = pd.DataFrame()
        if horse_names:
            ph2 = ','.join(['?'] * len(horse_names))
            g_df = pd.read_sql_query(f"SELECT * FROM gallops WHERE horse_name IN ({ph2})", conn, params=horse_names)
            
        # Feature Eng 
        def safe_enc(le, val):
            try: return le.transform([str(val)])[0]
            except: return 0
        df['track_encoded'] = df['track_type'].apply(lambda x: safe_enc(le_track, x))
        df['city_encoded'] = df['city'].apply(lambda x: safe_enc(le_city, x))
        
        # Hist (re-using connection)
        # We need a separate connection for get_historical to avoid threading issues if any (but here single thread)
        # But get_historical takes a connection.
        
        # Optimization: Do prediction for whole DF
        # ... (Omitting full feature eng code for brevity, assume similar to push_forecasts)
        # Actually need it to be accurate.
        
        # --- FEATURE ENG START ---
        m5_v = []; imp_v = []; com_v = []; trk_v = []; own_v = []; trn_v = []
        q_vecs = {k:[] for k in ['gold','fib','pri','cos','chaos','num','moon']}
        
        for idx, row in df.iterrows():
            m5, imp, com, trk, own, trn = get_historical_stats_v10(
                row['horse_name'], row['jockey'], row['track_type'], 
                row.get('trainer'), row.get('owner'), TARGET_DATE, conn=conn
            )
            m5_v.append(m5); imp_v.append(imp); com_v.append(com)
            trk_v.append(trk); own_v.append(own); trn_v.append(trn)
            
            rn = row['race_no'] or 1
            hn = row['horse_name'] or "X"
            q_vecs['gold'].append(golden_ratio_score(m5))
            q_vecs['fib'].append(fibonacci_resonance(rn, ord(hn[0])%10))
            q_vecs['pri'].append(prime_harmony(float(row['hp'] or 0), float(row['weight'] or 55)))
            q_vecs['cos'].append(cosmic_wave(TARGET_DATE, rn))
            q_vecs['chaos'].append(chaos_attractor(m5, com, trk))
            q_vecs['num'].append(numerology_score(hn))
            q_vecs['moon'].append(moon_phase(TARGET_DATE))
            
        df['momentum_5'] = m5_v; df['improvement_trend'] = imp_v
        df['combo_win_rate'] = com_v; df['track_win_rate'] = trk_v
        df['owner_win_rate'] = own_v; df['trainer_recent_form'] = trn_v
        df['trainer_win_rate_ext'] = 0.1
        for k in q_vecs: df[f'quantum_{"golden" if k=="gold" else "fibonacci" if k=="fib" else "prime" if k=="pri" else "cosmic" if k=="cos" else "chaos" if k=="chaos" else "numerology" if k=="num" else "moon"}'] = q_vecs[k]
        df['quantum_field'] = (df['quantum_golden']*PHI + df['quantum_fibonacci']*(FIBONACCI[7]/21) + df['quantum_prime']*math.pi + df['quantum_cosmic']*math.e + df['quantum_chaos']*2.718 + df['quantum_numerology']*7/9 + df['quantum_moon']*0.5)/10
        
        df = compute_galop_features(df, g_df, TARGET_DATE)
        
        features = ['distance', 'weight', 'track_encoded', 'city_encoded', 'hp',
            'momentum_5', 'improvement_trend', 'owner_win_rate', 'trainer_win_rate_ext', 'trainer_recent_form',
            'combo_win_rate', 'track_win_rate',
            'quantum_golden', 'quantum_fibonacci', 'quantum_prime', 'quantum_cosmic', 'quantum_chaos', 'quantum_numerology', 'quantum_moon', 'quantum_field',
            'days_since_galop', 'galop_speed']
            
        for f in features: 
            if f not in df.columns: df[f] = 0
            df[f] = pd.to_numeric(df[f], errors='coerce').fillna(0)
            
        # Filter (Same as push script)
        df['horse_name'] = df['horse_name'].str.strip()
        df = df[~df['horse_name'].str.contains('UNKNOWN', case=False, na=False)]
        df = df[~df['horse_name'].str.contains('VENTUS', case=False, na=False)]
        df['race_no'] = pd.to_numeric(df['race_no'], errors='coerce')

        X = df[features].astype(float)
        p = (lgbm.predict_proba(X)[:,1] + cat.predict_proba(X)[:,1] + xgb_model.predict_proba(X)[:,1]) / 3
        df['score'] = (p + (df['galop_score']-0.5)*0.2).clip(0,1)
        # --- FEATURE ENG END ---
        
        # Create Coupon (Last 6 Races)
        race_nos = sorted(df['race_no'].unique())
        legs = race_nos[-6:]
        legs_data = []
        for r in legs:
            entries = df[df['race_no'] == r].sort_values('score', ascending=False)
            legs_data.append([(x['horse_name'], x['score']) for _, x in entries.iterrows()])
            
        selection, cost = optimize_coupon_logic(legs_data, 700.0)
        
        # Compare
        caught_count = 0
        print(f"🎫 KUPON (Maliyet: {cost:.2f} TL)")
        
        for i, leg_sel in enumerate(selection):
            race_no = legs[i]
            # Find winner
            w_row = results_df[results_df['race_no'] == race_no]
            winner = w_row.iloc[0]['winner_name'].strip() if not w_row.empty else "???"
            
            my_horses = [x[0] for x in leg_sel]
            hit = winner in my_horses
            icon = "✅" if hit else "❌"
            if hit: caught_count += 1
            
            print(f"Koşu {race_no}: {icon} Kazanan: {winner:<20} | Bizimkiler: {', '.join(my_horses)}")
            
        print(f"\nSONUÇ: {caught_count}/6")
        if caught_count == 6: print("🏆 TEBRİKLER! ALTILI GANYAN TUTTU!")
        elif caught_count == 5: print("⚠️ 5'te Kaldık.")
        else: print("❌ Yattı.")
        
    conn.close()

if __name__ == "__main__":
    check_success()
