
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
    golden_ratio_score, fibonacci_resonance, prime_harmony,
    cosmic_wave, chaos_attractor, numerology_score, moon_phase,
    PHI, FIBONACCI
)

DB_NAME = "tjk_races.db"
TARGET_DATE = "16/01/2026"
TARGET_CITY = "Antalya"
TARGET_RACE_NO = 5 # Leg 3

def analyze_race():
    print(f"🔮 Analyzing {TARGET_CITY} Race {TARGET_RACE_NO} (Why CASH FOR YOU?)...")
    
    # Load Models
    try:
        lgbm = joblib.load('model_honest_lgbm.pkl')
        cat = joblib.load('model_honest_cat.pkl')
        xgb_model = joblib.load('model_honest_xgb.pkl')
        le_track = joblib.load('le_track_honest.pkl')
        le_city = joblib.load('le_city_honest.pkl')
    except: return

    conn = sqlite3.connect(DB_NAME)
    
    # Fetch Specific Race ID for Antalya, Race 5
    pr_query = f"""
        SELECT id, city, date FROM program_races 
        WHERE date='{TARGET_DATE}' AND city LIKE '%{TARGET_CITY}%' AND race_no={TARGET_RACE_NO}
    """
    pr_df = pd.read_sql_query(pr_query, conn)
    race_id = pr_df.iloc[0]['id']
    
    # Fetch Entries
    entries_query = f"""
        SELECT pe.*, pr.race_no, pr.date, pr.city, pr.distance, pr.track_type
        FROM program_entries pe
        JOIN program_races pr ON pe.program_race_id = pr.id
        WHERE pr.id = {race_id}
    """
    df = pd.read_sql_query(entries_query, conn)
    
    # Galop
    horse_names = tuple(df['horse_name'].dropna().unique().tolist())
    if horse_names:
        placeholders = ','.join(['?'] * len(horse_names))
        g_df = pd.read_sql_query(f"SELECT * FROM gallops WHERE horse_name IN ({placeholders})", conn, params=horse_names)
    else: g_df = pd.DataFrame()
    conn.close()
    
    # Feature Eng (Simplified)
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
        
        # Quantum
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
    
    df['momentum_5'] = m5_v
    df['improvement_trend'] = imp_v
    df['combo_win_rate'] = com_v
    df['track_win_rate'] = trk_v
    df['owner_win_rate'] = own_v
    df['trainer_recent_form'] = trn_v
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
    
    results = df.sort_values('score', ascending=False)
    
    print("\n🏁 DETAYLI ANALİZ:")
    print("-" * 80)
    print(f"{'AT ADI':<15} | {'SKOR':<5} | {'FORM':<5} | {'PİST%':<5} | {'GALOP':<5} | {'JOKEY%':<5} | {'QUANTUM':<5}")
    print("-" * 80)
    for i, row in results.iterrows():
        print(f"{row['horse_name']:<15} | {row['score']:.2f}  | {row['momentum_5']:.2f}  | {row['track_win_rate']:.2f}   | {row['galop_score']:.2f}   | {row['combo_win_rate']:.2f}   | {row['quantum_field']:.2f}")

if __name__ == "__main__":
    analyze_race()
