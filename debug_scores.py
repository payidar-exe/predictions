
import sqlite3
import pandas as pd
import joblib
import sys
import os
import math

sys.path.append(os.getcwd())
from production_engine import (
    get_historical_stats_v10,
    compute_galop_features,
    optimize_coupon_logic
)

DB_NAME = "tjk_races.db"
TARGET_DATE = "19/01/2026"

def debug_scores():
    lgbm = joblib.load('model_honest_lgbm.pkl')
    cat = joblib.load('model_honest_cat.pkl')
    xgb_model = joblib.load('model_honest_xgb.pkl')
    le_track = joblib.load('le_track_honest.pkl')
    le_city = joblib.load('le_city_honest.pkl')
    
    conn = sqlite3.connect(DB_NAME)
    pr_df = pd.read_sql_query(f"SELECT * FROM program_races WHERE date='{TARGET_DATE}' AND city LIKE '%Bursa%'", conn)
    race_ids = tuple(pr_df['id'].tolist())
    df = pd.read_sql_query(f"SELECT pe.*, pr.race_no, pr.date, pr.city, pr.distance, pr.track_type FROM program_entries pe JOIN program_races pr ON pe.program_race_id = pr.id WHERE pr.id IN {race_ids}", conn)
    
    def safe_enc(le, val):
        try: return le.transform([str(val)])[0]
        except: return 0
    df['track_encoded'] = df['track_type'].apply(lambda x: safe_enc(le_track, x))
    df['city_encoded'] = df['city'].apply(lambda x: safe_enc(le_city, x))
    
    # Minimal features for check
    df['hp'] = pd.to_numeric(df['hp'], errors='coerce').fillna(0)
    df['weight'] = pd.to_numeric(df['weight'], errors='coerce').fillna(55)
    df['distance'] = pd.to_numeric(df['distance'], errors='coerce').fillna(1400)
    
    features = ['distance', 'weight', 'track_encoded', 'city_encoded', 'hp',
                'momentum_5', 'improvement_trend', 'owner_win_rate', 
                'trainer_win_rate_ext', 'trainer_recent_form', 'combo_win_rate', 'track_win_rate',
                'quantum_golden', 'quantum_fibonacci', 'quantum_prime',
                'quantum_cosmic', 'quantum_chaos', 'quantum_numerology', 
                'quantum_moon', 'quantum_field',
                'days_since_galop', 'galop_speed']
                
    for f in features:
        if f not in df.columns: df[f] = 0
        df[f] = pd.to_numeric(df[f], errors='coerce').fillna(0)
        
    X = df[features].astype(float)
    p = (lgbm.predict_proba(X)[:,1] + cat.predict_proba(X)[:,1] + xgb_model.predict_proba(X)[:,1]) / 3
    df['score'] = p
    
    print(f"Debug Bursa Scores (First 10):")
    print(df[['horse_name', 'score', 'race_no']].head(10))
    print(f"Any NaN scores? {df['score'].isna().any()}")
    print(f"Score describe:\n{df['score'].describe()}")

if __name__ == "__main__":
    debug_scores()
