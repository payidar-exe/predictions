
import sqlite3
import pandas as pd
import numpy as np
import joblib
import lightgbm as lgb
import xgboost as xgb
from catboost import CatBoostClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import LabelEncoder
import math
from datetime import datetime, timedelta
import sys
import os

# Import production engine components for feature calc (to stay consistent)
# Actually, train_model_v10_kahin has its own definitions.
# We will copy-paste necessary parts to ensure isolation or importing if clean.
# Let's import from train_model_v10_kahin actually (if possible) or just duplicate logic.
# Duplicating logic is safer to modify filtering without breaking original file.

sys.path.append(os.getcwd())
# We will just replicate the logic from train_model_v10_kahin but add date filtering.

DB_NAME = "tjk_races.db"
# Constants
PHI = 1.6180339887
FIBONACCI = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]

def golden_ratio_score(value): return (value * PHI) % 1.0
def fibonacci_resonance(race_no, horse_no): return FIBONACCI[(race_no + horse_no) % len(FIBONACCI)] / 144.0
def prime_harmony(hp, weight):
    ratio = hp / max(weight, 1)
    closest_prime = min(PRIMES, key=lambda p: abs(p - ratio * 10))
    return 1.0 / (1.0 + abs(closest_prime - ratio * 10))
def cosmic_wave(date_str, race_no):
    try: day, month = int(date_str.split('/')[0]), int(date_str.split('/')[1])
    except: day, month = 1, 1
    phase = (day * 12.368 + month * 30.4375 + race_no * PHI) * (2 * math.pi / 365)
    return (math.sin(phase) + 1) / 2
def chaos_attractor(momentum, combo_rate, track_rate):
    x, y, z = momentum * 10, combo_rate * 10, track_rate * 10
    dx = 10.0 * (y - x); dy = x * (28.0 - z) - y; dz = x * y - (8/3) * z
    return (abs(dx + dy + dz) % 100) / 100.0
def numerology_score(horse_name):
    total = sum(ord(c) for c in horse_name.upper() if c.isalpha())
    while total > 9: total = sum(int(d) for d in str(total))
    return total / 9.0
def moon_phase(date_str):
    try: day, month = int(date_str.split('/')[0]), int(date_str.split('/')[1])
    except: day, month = 1, 1
    lunar = (day + month * 2) % 30
    return (math.sin(lunar * math.pi / 15) + 1) / 2

def build_extended_features(days_back=5):
    print("🔮 REAL BACKTEST: Preparing Data (Honest Mode)")
    print("=" * 70)
    
    conn = sqlite3.connect(DB_NAME)
    results_df = pd.read_sql_query("""
        SELECT 
            res.id, res.horse_name, res.jockey, res.owner, res.trainer,
            res.rank, res.weight, res.hp,
            r.date, r.city, r.distance, r.track_type, r.race_no
        FROM results res
        JOIN races r ON res.race_id = r.id
        ORDER BY r.date, r.id
    """, conn)
    
    # Parse dates
    results_df['race_date_dt'] = pd.to_datetime(results_df['date'], dayfirst=True, errors='coerce')
    
    # Determine Cutoff
    today = datetime.now()
    cutoff_date = today - timedelta(days=days_back)
    print(f"📅 Cutoff Date: {cutoff_date.strftime('%Y-%m-%d')} (Excluding data after this)")
    
    # SPLIT: Training Data vs Test Data
    # Training Data: Only BEFORE Cutoff
    # We will compute features using ALL data (history is naturally past), 
    # but when doing 'train_test_split' later, we will be strict.
    
    # Actually, if we compute history using "future" races, it's leakage.
    # But get_historical_stats logic iterates row by row. If we sort by date, 
    # and compute rolling stats, it naturally respects time (past only).
    # Since we are using manual rolling calculation here (iterating DF sorted by date),
    # history features are inherently honest (only past races seen so far).
    
    # So we can compute features on FULL dataset, but then FILTER for Training.
    
    # ... (Feature Engineering: Same as original) ...
    # Simplified copy-paste of logic for speed
    
    print("\n📈 Calculating 'Son 5 Yarış Trendi'...")
    results_df['last_5_avg'] = 0.0; results_df['improvement_trend'] = 0.0
    horse_history = {}
    for idx, row in results_df.iterrows():
        horse = row['horse_name']
        rank = row['rank'] if row['rank'] and row['rank'] > 0 else 10
        if horse in horse_history and len(horse_history[horse]) >= 2:
            last_5 = horse_history[horse][-5:]
            avg = np.mean(last_5)
            results_df.at[idx, 'last_5_avg'] = avg
            if len(last_5) >= 5:
                results_df.at[idx, 'improvement_trend'] = (np.mean(last_5[:3]) - np.mean(last_5[-2:])) / 10
        if horse not in horse_history: horse_history[horse] = []
        horse_history[horse].append(rank)
    results_df['momentum_5'] = (10 - results_df['last_5_avg'].clip(upper=10)) / 10
    
    # Owner Stats
    owner_stats = {}; results_df['owner_win_rate'] = 0.0
    for idx, row in results_df.iterrows():
        owner = row['owner']; is_win = 1 if row['rank'] == 1 else 0
        if owner in owner_stats: w, t = owner_stats[owner]; results_df.at[idx, 'owner_win_rate'] = w/t
        else: owner_stats[owner] = (0, 0)
        owner_stats[owner] = (owner_stats[owner][0]+is_win, owner_stats[owner][1]+1)

    # Trainer Stats
    trn_stats = {}; results_df['trainer_win_rate_ext'] = 0.0; results_df['trainer_recent_form'] = 0.0
    for idx, row in results_df.iterrows():
        trn = row['trainer']; is_win = 1 if row['rank'] == 1 else 0
        if trn in trn_stats:
            w, t, r = trn_stats[trn]; results_df.at[idx, 'trainer_win_rate_ext'] = w/t
            results_df.at[idx, 'trainer_recent_form'] = np.mean(r[-10:]) if r else 0
        else: trn_stats[trn] = (0, 0, [])
        trn_stats[trn] = (trn_stats[trn][0]+is_win, trn_stats[trn][1]+1, trn_stats[trn][2]+[is_win])
        
    # Combo & Track
    com_hist = {}; trk_hist = {}; results_df['combo_win_rate'] = 0.0; results_df['track_win_rate'] = 0.0
    for idx, row in results_df.iterrows():
        h = row['horse_name']; j = row['jockey']; trk = row['track_type'] if row['track_type'] else 'Unknown'
        win = 1 if row['rank'] == 1 else 0
        ck = f"{h}|||{j}"
        if ck in com_hist: results_df.at[idx, 'combo_win_rate'] = com_hist[ck][0]/com_hist[ck][1]
        else: com_hist[ck] = (0, 0)
        com_hist[ck] = (com_hist[ck][0]+win, com_hist[ck][1]+1)
        
        if h not in trk_hist: trk_hist[h] = {}
        if trk in trk_hist[h]: results_df.at[idx, 'track_win_rate'] = trk_hist[h][trk][0]/trk_hist[h][trk][1]
        else: trk_hist[h][trk] = (0, 0)
        trk_hist[h][trk] = (trk_hist[h][trk][0]+win, trk_hist[h][trk][1]+1)

    # Quantum
    results_df['quantum_golden'] = results_df['momentum_5'].apply(golden_ratio_score)
    results_df['quantum_fibonacci'] = results_df.apply(lambda r: fibonacci_resonance(r['race_no'] or 1, ord(r['horse_name'][0])%10), axis=1)
    results_df['hp'] = pd.to_numeric(results_df['hp'], errors='coerce').fillna(0)
    results_df['weight'] = pd.to_numeric(results_df['weight'], errors='coerce').fillna(55)
    results_df['quantum_prime'] = results_df.apply(lambda r: prime_harmony(r['hp'], r['weight']), axis=1)
    results_df['quantum_cosmic'] = results_df.apply(lambda r: cosmic_wave(str(r['date']), r['race_no'] or 1), axis=1)
    results_df['quantum_chaos'] = results_df.apply(lambda r: chaos_attractor(r['momentum_5'], r['combo_win_rate'], r['track_win_rate']), axis=1)
    results_df['quantum_numerology'] = results_df['horse_name'].apply(numerology_score)
    results_df['quantum_moon'] = results_df['date'].apply(lambda d: moon_phase(str(d)))
    
    results_df['quantum_field'] = (
        results_df['quantum_golden'] * PHI +
        results_df['quantum_fibonacci'] * FIBONACCI[7] / 21 +
        results_df['quantum_prime'] * math.pi +
        results_df['quantum_cosmic'] * math.e +
        results_df['quantum_chaos'] * 2.71828 +
        results_df['quantum_numerology'] * 7 / 9 +
        results_df['quantum_moon'] * 0.5
    ) / 10.0
    
    # Galop
    print("🏇 Integrating GALOP data...")
    try:
        gallops_df = pd.read_sql_query("SELECT horse_name, date, distance, time_sec FROM gallops", conn)
        if not gallops_df.empty:
            gallops_df['gal_date'] = pd.to_datetime(gallops_df['date'], dayfirst=True, errors='coerce')
            gallops_df = gallops_df.dropna(subset=['gal_date']).sort_values('gal_date')
            results_df = results_df.sort_values('race_date_dt')
            
            merged = pd.merge_asof(
                results_df, gallops_df,
                left_on='race_date_dt', right_on='gal_date',
                by='horse_name', direction='backward'
            )
            merged['days_since_galop'] = (merged['race_date_dt'] - merged['gal_date']).dt.days
            merged['galop_speed'] = merged['distance_y'] / merged['time_sec']
            results_df['days_since_galop'] = merged['days_since_galop'].fillna(999)
            results_df['galop_speed'] = merged['galop_speed'].fillna(0)
        else:
            results_df['days_since_galop'] = 999; results_df['galop_speed'] = 0
    except:
        results_df['days_since_galop'] = 999; results_df['galop_speed'] = 0
    conn.close()

    # Encode
    le_track = LabelEncoder()
    le_city = LabelEncoder()
    results_df['track_encoded'] = le_track.fit_transform(results_df['track_type'].fillna('Unknown').astype(str))
    results_df['city_encoded'] = le_city.fit_transform(results_df['city'].fillna('Unknown').astype(str))
    results_df['is_winner'] = (results_df['rank'] == 1).astype(int)
    results_df['distance'] = pd.to_numeric(results_df['distance'], errors='coerce').fillna(1400)
    
    # FILTER FOR HONEST TRAINING
    # Train = Before Cutoff
    # Test (Implicit) = After Cutoff (User will verify manually or via separate script)
    # We only return TRAIN data here to train the model.
    
    train_df = results_df[results_df['race_date_dt'] < cutoff_date].copy()
    print(f"\n✂️ Filtered Training Data: {len(train_df)} rows (Total was {len(results_df)})")
    
    return train_df, le_track, le_city

def train_honest_model(df, le_track, le_city):
    print("\n🧠 TRAINING HONEST MODEL (No Peeking at last 5 days)")
    
    features = [
        'distance', 'weight', 'track_encoded', 'city_encoded', 'hp',
        'momentum_5', 'improvement_trend', 'owner_win_rate', 'trainer_win_rate_ext', 'trainer_recent_form',
        'combo_win_rate', 'track_win_rate',
        'quantum_golden', 'quantum_fibonacci', 'quantum_prime', 'quantum_cosmic', 'quantum_chaos', 'quantum_numerology', 'quantum_moon', 'quantum_field',
        'days_since_galop', 'galop_speed'
    ]
    
    for col in features: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df = df.dropna(subset=['is_winner'])
    
    X = df[features].astype(float)
    y = df['is_winner']
    
    # Train/Validation Split (Internal Valid)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # LightGBM
    lgbm = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.03, num_leaves=47, random_state=42, verbose=-1)
    lgbm.fit(X_train, y_train)
    
    # CatBoost
    cat = CatBoostClassifier(iterations=700, learning_rate=0.03, depth=7, verbose=False, random_state=42, allow_writing_files=False)
    cat.fit(X_train, y_train)
    
    # XGBoost
    xgb_model = xgb.XGBClassifier(n_estimators=300, learning_rate=0.03, max_depth=7, eval_metric='logloss', random_state=42)
    xgb_model.fit(X_train, y_train)
    
    auc = roc_auc_score(y_val, (lgbm.predict_proba(X_val)[:,1] + cat.predict_proba(X_val)[:,1] + xgb_model.predict_proba(X_val)[:,1])/3)
    print(f"✅ Honest Validation AUC: {auc:.4f}")
    
    # Save as 'honest' models
    joblib.dump(lgbm, 'model_honest_lgbm.pkl')
    joblib.dump(cat, 'model_honest_cat.pkl')
    joblib.dump(xgb_model, 'model_honest_xgb.pkl')
    # Save encoders too (important!)
    joblib.dump(le_track, 'le_track_honest.pkl')
    joblib.dump(le_city, 'le_city_honest.pkl')
    print("🔒 Honest Models Saved.")

if __name__ == "__main__":
    train_data, lt, lc = build_extended_features(days_back=5)
    train_honest_model(train_data, lt, lc)
