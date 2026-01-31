
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
TARGET_CITY_KEY = "Gulfstream"
TARGET_RACES = [5, 6, 7, 8, 9] # 5'li Ganyan Legs
BUDGET = 280.0

def generate_5li():
    print(f"🔮 Generating 5'li Ganyan for {TARGET_CITY_KEY} ({TARGET_DATE})...")
    
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
    
    # Fetch Races
    pr_query = f"""
        SELECT id, city, date, race_no, time FROM program_races 
        WHERE date='{TARGET_DATE}' AND city LIKE '%{TARGET_CITY_KEY}%'
    """
    pr_df = pd.read_sql_query(pr_query, conn)
    
    if pr_df.empty:
        print("❌ No races found.")
        return
        
    # Filter for target races
    pr_df = pr_df[pr_df['race_no'].isin(TARGET_RACES)]
    race_ids = tuple(pr_df['id'].tolist())
    
    # Fetch Entries
    placeholders = ','.join(['?'] * len(race_ids))
    entries_query = f"""
        SELECT pe.*, pr.race_no, pr.date, pr.city, pr.distance, pr.track_type, pr.time
        FROM program_entries pe
        JOIN program_races pr ON pe.program_race_id = pr.id
        WHERE pr.id IN ({placeholders})
    """
    df = pd.read_sql_query(entries_query, conn, params=race_ids)
    
    # Galop
    horse_names = tuple(df['horse_name'].dropna().unique().tolist())
    if horse_names:
        ph2 = ','.join(['?'] * len(horse_names))
        g_df = pd.read_sql_query(f"SELECT * FROM gallops WHERE horse_name IN ({ph2})", conn, params=horse_names)
    else: g_df = pd.DataFrame()
    conn.close()
    
    # Feature Eng
    def safe_enc(le, val):
        try: return le.transform([str(val)])[0]
        except: return 0
    df['track_encoded'] = df['track_type'].apply(lambda x: safe_enc(le_track, x))
    df['city_encoded'] = df['city'].apply(lambda x: safe_enc(le_city, x))
    
    conn = sqlite3.connect(DB_NAME)
    m5_v, imp_v, com_v, trk_v, own_v, trn_v = [], [], [], [], [], []
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
    conn.close()
    
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
        
    X = df[features].astype(float)
    p = (lgbm.predict_proba(X)[:,1] + cat.predict_proba(X)[:,1] + xgb_model.predict_proba(X)[:,1]) / 3
    df['score'] = (p + (df['galop_score']-0.5)*0.2).clip(0,1)
    
    # --- OPTIMIZE ---
    legs_data = []
    # Ensure order 5, 6, 7, 8, 9
    for r in TARGET_RACES:
        entries = df[df['race_no'] == r].sort_values('score', ascending=False)
        legs_data.append([(x['horse_name'], x['score'], x['jockey'], x['momentum_5']) for _, x in entries.iterrows()])
        
    # Wrapper for logic because logic expects tuples of (name, score)
    # Actually logic works on list, but returns list.
    # We pass standard structure and then map back.
    
    # Simplification: optimize_coupon_logic returns 'selection' which is list of items from input list.
    # So if I pass tuples with extra info, it should return them back.
    
    selection, cost = optimize_coupon_logic(legs_data, budget_tl=BUDGET)
    
    print("\n🇺🇸 GULFSTREAM PARK 5'Lİ GANYAN TAHMİNİ")
    print(f"💰 Bütçe: {BUDGET} TL | Tahmini Tutar: {cost:.2f} TL")
    print("=" * 60)
    
    for i, leg_sel in enumerate(selection):
        race_no = TARGET_RACES[i]
        print(f"📍 {i+1}. Ayak (Koşu {race_no}):")
        
        # Sort selection by score descending for display
        leg_sel.sort(key=lambda x: x[1], reverse=True)
        
        line = ""
        for horse in leg_sel:
            # horse is (name, score, jockey, form)
            line += f"{horse[0]} ({horse[1]:.2f}), "
        print(f"   {line.strip(', ')}")
        print("-" * 60)

if __name__ == "__main__":
    generate_5li()
