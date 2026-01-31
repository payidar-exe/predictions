
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

DB_NAME = "tjk_races.db"

# ═══════════════════════════════════════════════════════════════════
# 🔮 QUANTUM CONSTANTS (Parallel Universe Parameters)
# ═══════════════════════════════════════════════════════════════════

PHI = 1.6180339887  # Golden Ratio (Altın Oran)
FIBONACCI = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]  # Sacred Sequence
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]  # Prime Resonance

def golden_ratio_score(value):
    """Apply Golden Ratio transformation - Universe's favorite number"""
    return (value * PHI) % 1.0

def fibonacci_resonance(race_no, horse_no):
    """Calculate Fibonacci resonance between race and horse number"""
    fib_idx = (race_no + horse_no) % len(FIBONACCI)
    return FIBONACCI[fib_idx] / 144.0  # Normalize

def prime_harmony(hp, weight):
    """Check if HP/Weight ratio aligns with prime numbers"""
    ratio = hp / max(weight, 1)
    closest_prime = min(PRIMES, key=lambda p: abs(p - ratio * 10))
    return 1.0 / (1.0 + abs(closest_prime - ratio * 10))  # Higher = better alignment

def cosmic_wave(date_str, race_no):
    """Sinusoidal wave based on date and race - Cosmic Rhythm"""
    try:
        day = int(date_str.split('/')[0])
        month = int(date_str.split('/')[1])
    except:
        day, month = 1, 1
    
    phase = (day * 12.368 + month * 30.4375 + race_no * PHI) * (2 * math.pi / 365)
    return (math.sin(phase) + 1) / 2  # Normalize to 0-1

def chaos_attractor(momentum, combo_rate, track_rate):
    """Lorenz-inspired chaos attractor - Sensitive to initial conditions"""
    sigma, rho, beta = 10.0, 28.0, 8.0/3.0
    
    x = momentum * 10
    y = combo_rate * 10
    z = track_rate * 10
    
    # One step of Lorenz system
    dx = sigma * (y - x)
    dy = x * (rho - z) - y
    dz = x * y - beta * z
    
    # Combine into a score (0-1)
    chaos_val = abs(dx + dy + dz) % 100
    return chaos_val / 100.0

def numerology_score(horse_name):
    """Ancient numerology based on horse name"""
    total = sum(ord(c) for c in horse_name.upper() if c.isalpha())
    # Reduce to single digit (Pythagorean method)
    while total > 9:
        total = sum(int(d) for d in str(total))
    return total / 9.0  # Normalize

def moon_phase(date_str):
    """Approximate moon phase influence (Lunar cycle ~29.5 days)"""
    try:
        day = int(date_str.split('/')[0])
        month = int(date_str.split('/')[1])
    except:
        day, month = 1, 1
    # Approximation based on day of month
    lunar_day = (day + month * 2) % 30
    phase = math.sin(lunar_day * math.pi / 15)  # Full moon at 15
    return (phase + 1) / 2

# ═══════════════════════════════════════════════════════════════════
# 📊 EXTENDED DATA FEATURES 
# ═══════════════════════════════════════════════════════════════════

def build_extended_features():
    print("🔮 MODEL v10: QUANTUM + EXTENDED DATA")
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
    
    print(f"Loaded {len(results_df)} race results")
    
    # --- EXTENDED: SON 5 YARIŞ TRENDİ ---
    print("\n📈 Calculating 'Son 5 Yarış Trendi'...")
    results_df['last_5_avg'] = 0.0
    results_df['improvement_trend'] = 0.0
    
    horse_history = {}
    
    for idx, row in results_df.iterrows():
        horse = row['horse_name']
        rank = row['rank'] if row['rank'] and row['rank'] > 0 else 10
        
        if horse in horse_history and len(horse_history[horse]) >= 2:
            last_5 = horse_history[horse][-5:]
            avg = np.mean(last_5)
            results_df.at[idx, 'last_5_avg'] = avg
            
            # Improvement trend (son 2 yarış vs önceki 3)
            if len(last_5) >= 5:
                recent_avg = np.mean(last_5[-2:])
                older_avg = np.mean(last_5[:3])
                results_df.at[idx, 'improvement_trend'] = (older_avg - recent_avg) / 10  # Positive = improving
        
        if horse not in horse_history:
            horse_history[horse] = []
        horse_history[horse].append(rank)
    
    results_df['momentum_5'] = (10 - results_df['last_5_avg'].clip(upper=10)) / 10
    
    # --- EXTENDED: SAHİP (OWNER) İSTATİSTİKLERİ ---
    print("👔 Calculating 'Sahip (Owner) Stats'...")
    owner_stats = {}
    results_df['owner_win_rate'] = 0.0
    results_df['owner_races'] = 0
    
    for idx, row in results_df.iterrows():
        owner = row['owner']
        is_win = 1 if row['rank'] == 1 else 0
        
        if owner and owner in owner_stats:
            w, t = owner_stats[owner]
            results_df.at[idx, 'owner_win_rate'] = w / t if t > 0 else 0
            results_df.at[idx, 'owner_races'] = t
        
        if owner:
            if owner not in owner_stats:
                owner_stats[owner] = (0, 0)
            w, t = owner_stats[owner]
            owner_stats[owner] = (w + is_win, t + 1)
    
    # --- EXTENDED: ANTRENÖR (TRAINER) DETAYLARI ---
    print("🏋️ Calculating 'Antrenör (Trainer) Detailed Stats'...")
    trainer_stats = {}
    results_df['trainer_win_rate_ext'] = 0.0
    results_df['trainer_recent_form'] = 0.0
    
    for idx, row in results_df.iterrows():
        trainer = row['trainer']
        is_win = 1 if row['rank'] == 1 else 0
        
        if trainer and trainer in trainer_stats:
            wins, total, recent = trainer_stats[trainer]
            results_df.at[idx, 'trainer_win_rate_ext'] = wins / total if total > 0 else 0
            # Recent form = Last 10 races win rate
            results_df.at[idx, 'trainer_recent_form'] = np.mean(recent[-10:]) if recent else 0
        
        if trainer:
            if trainer not in trainer_stats:
                trainer_stats[trainer] = (0, 0, [])
            w, t, r = trainer_stats[trainer]
            trainer_stats[trainer] = (w + is_win, t + 1, r + [is_win])
    
    # --- AT-JOKEY COMBO (v9'dan) ---
    print("🤝 Calculating 'At-Jokey Combo'...")
    combo_history = {}
    results_df['combo_win_rate'] = 0.0
    
    for idx, row in results_df.iterrows():
        horse = row['horse_name']
        jockey = row['jockey']
        is_win = 1 if row['rank'] == 1 else 0
        combo_key = f"{horse}|||{jockey}"
        
        if combo_key in combo_history:
            wins, total = combo_history[combo_key]
            results_df.at[idx, 'combo_win_rate'] = wins / total if total > 0 else 0
        
        if combo_key not in combo_history:
            combo_history[combo_key] = (0, 0)
        w, t = combo_history[combo_key]
        combo_history[combo_key] = (w + is_win, t + 1)
    
    # --- PİST TERCİHİ (v9'dan) ---
    print("🏁 Calculating 'Pist Tercihi'...")
    track_history = {}
    results_df['track_win_rate'] = 0.0
    
    for idx, row in results_df.iterrows():
        horse = row['horse_name']
        track = row['track_type'] if row['track_type'] else 'Unknown'
        is_win = 1 if row['rank'] == 1 else 0
        
        if horse in track_history and track in track_history[horse]:
            wins, total = track_history[horse][track]
            results_df.at[idx, 'track_win_rate'] = wins / total if total > 0 else 0
        
        if horse not in track_history:
            track_history[horse] = {}
        if track not in track_history[horse]:
            track_history[horse][track] = (0, 0)
        w, t = track_history[horse][track]
        track_history[horse][track] = (w + is_win, t + 1)
    
    # ═══════════════════════════════════════════════════════════════
    # 🔮 QUANTUM FEATURES
    # ═══════════════════════════════════════════════════════════════
    print("\n🌌 Applying QUANTUM TRANSFORMATIONS...")
    
    results_df['quantum_golden'] = results_df['momentum_5'].apply(golden_ratio_score)
    
    results_df['quantum_fibonacci'] = results_df.apply(
        lambda r: fibonacci_resonance(r['race_no'] if r['race_no'] else 1, 
                                       ord(r['horse_name'][0]) % 10 if r['horse_name'] else 1), 
        axis=1
    )
    
    results_df['hp'] = pd.to_numeric(results_df['hp'], errors='coerce').fillna(0)
    results_df['weight'] = pd.to_numeric(results_df['weight'], errors='coerce').fillna(55)
    
    results_df['quantum_prime'] = results_df.apply(
        lambda r: prime_harmony(r['hp'], r['weight']), axis=1
    )
    
    results_df['quantum_cosmic'] = results_df.apply(
        lambda r: cosmic_wave(str(r['date']), r['race_no'] if r['race_no'] else 1), axis=1
    )
    
    results_df['quantum_chaos'] = results_df.apply(
        lambda r: chaos_attractor(r['momentum_5'], r['combo_win_rate'], r['track_win_rate']), axis=1
    )
    
    results_df['quantum_numerology'] = results_df['horse_name'].apply(numerology_score)
    
    results_df['quantum_moon'] = results_df['date'].apply(lambda d: moon_phase(str(d)))
    
    # --- MEGA QUANTUM INTERACTION ---
    print("🌀 Creating QUANTUM INTERACTION FIELD...")
    results_df['quantum_field'] = (
        results_df['quantum_golden'] * PHI +
        results_df['quantum_fibonacci'] * FIBONACCI[7] / 21 +
        results_df['quantum_prime'] * math.pi +
        results_df['quantum_cosmic'] * math.e +
        results_df['quantum_chaos'] * 2.71828 +
        results_df['quantum_numerology'] * 7 / 9 +
        results_df['quantum_moon'] * 0.5
    ) / 10.0  # Normalize to ~0-1
    
    # --- GALOP INTEGRATION (v10.5) ---
    print("🏇 Integrating GALOP data...")
    try:
        gallops_df = pd.read_sql_query("SELECT horse_name, date, distance, time_sec FROM gallops", conn)
        
        if not gallops_df.empty:
            # Prepare Dates
            # TJK saves as dd.mm.yyyy, Races are dd/mm/yyyy or yyyy-mm-dd
            # Use coerce to handle errors
            gallops_df['gal_date'] = pd.to_datetime(gallops_df['date'], dayfirst=True, errors='coerce')
            results_df['race_date_dt'] = pd.to_datetime(results_df['date'], dayfirst=True, errors='coerce')
            
            # Drop invalid dates
            gallops_df = gallops_df.dropna(subset=['gal_date'])
            gallops_df = gallops_df.sort_values('gal_date')
            
            results_df = results_df.sort_values('race_date_dt')
            
            # Merge Asof (match last galop before race)
            # Must merge by horse_name (exact match)
            # merge_asof requires sorting by ON column
            
            # Since merge_asof 'by' must be exact, horse names must be normalized.
            # Assuming DB names are consistent.
            
            # We need to map horse_name to IDs or just use horse_name as group key.
            # Pandas merge_asof supports 'by' argument.
            
            merged_gal = pd.merge_asof(
                results_df,
                gallops_df,
                left_on='race_date_dt',
                right_on='gal_date',
                by='horse_name',
                direction='backward'
            )
            
            # Calculate Features
            merged_gal['days_since_galop'] = (merged_gal['race_date_dt'] - merged_gal['gal_date']).dt.days
            merged_gal['galop_speed'] = merged_gal['distance_y'] / merged_gal['time_sec'] # dist_y is galop dist
            
            # Fill NaNs
            merged_gal['days_since_galop'] = merged_gal['days_since_galop'].fillna(999)
            merged_gal['galop_speed'] = merged_gal['galop_speed'].fillna(0)
            
            # Update results_df
            # Since we sorted results_df, the index might have shuffled. 
            # merge_asof preserves left index order if left is sorted? No, it returns new DF.
            # We replace results_df columns
            results_df['days_since_galop'] = merged_gal['days_since_galop']
            results_df['galop_speed'] = merged_gal['galop_speed']
            
            print(f"   Integrated galops for {len(gallops_df)} records.")
            
        else:
            print("   ⚠️ No galop data found in DB.")
            results_df['days_since_galop'] = 999
            results_df['galop_speed'] = 0
            
    except Exception as e:
        print(f"   ❌ Galop Integration Error: {e}")
        results_df['days_since_galop'] = 999
        results_df['galop_speed'] = 0

    conn.close()
    
    # --- SAVE ---
    results_df['is_winner'] = (results_df['rank'] == 1).astype(int)
    results_df['distance'] = pd.to_numeric(results_df['distance'], errors='coerce').fillna(1400)
    
    le_track = LabelEncoder()
    le_city = LabelEncoder()
    
    results_df['track_encoded'] = le_track.fit_transform(results_df['track_type'].fillna('Unknown').astype(str))
    results_df['city_encoded'] = le_city.fit_transform(results_df['city'].fillna('Unknown').astype(str))
    
    results_df.to_csv('features_dataset_v10.csv', index=False)
    print(f"\n💾 Saved features_dataset_v10.csv ({len(results_df)} rows)")
    
    return results_df, le_track, le_city

def train_model_v10(df, le_track, le_city):
    print("\n🧠 TRAINING MODEL v10 (Kahin - The Oracle)")
    print("=" * 70)
    
    features = [
        # Standard
        'distance', 'weight', 'track_encoded', 'city_encoded', 'hp',
        # Extended
        'momentum_5', 'improvement_trend',
        'owner_win_rate', 'trainer_win_rate_ext', 'trainer_recent_form',
        'combo_win_rate', 'track_win_rate',
        # Quantum
        'quantum_golden', 'quantum_fibonacci', 'quantum_prime',
        'quantum_cosmic', 'quantum_chaos', 'quantum_numerology', 
        'quantum_moon', 'quantum_field',
        # Galop (v10.5)
        'days_since_galop', 'galop_speed'
    ]
    
    for col in features:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    df = df.dropna(subset=['is_winner'])
    X = df[features].astype(float)
    y = df['is_winner']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print(f"Training: {len(X_train)} | Test: {len(X_test)}")
    
    # --- LightGBM ---
    print("\n⚡ Training LightGBM...")
    lgbm = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.03, num_leaves=47, random_state=42, verbose=-1)
    lgbm.fit(X_train, y_train)
    p_lgbm = lgbm.predict_proba(X_test)[:, 1]
    auc_lgbm = roc_auc_score(y_test, p_lgbm)
    print(f"   LightGBM AUC: {auc_lgbm:.4f}")
    
    # --- CatBoost ---
    print("\n🐱 Training CatBoost...")
    cat = CatBoostClassifier(iterations=700, learning_rate=0.03, depth=7, verbose=False, random_state=42, allow_writing_files=False)
    cat.fit(X_train, y_train)
    p_cat = cat.predict_proba(X_test)[:, 1]
    auc_cat = roc_auc_score(y_test, p_cat)
    print(f"   CatBoost AUC: {auc_cat:.4f}")
    
    # --- XGBoost ---
    print("\n🌳 Training XGBoost...")
    xgb_model = xgb.XGBClassifier(n_estimators=300, learning_rate=0.03, max_depth=7, eval_metric='logloss', random_state=42)
    xgb_model.fit(X_train, y_train)
    p_xgb = xgb_model.predict_proba(X_test)[:, 1]
    auc_xgb = roc_auc_score(y_test, p_xgb)
    print(f"   XGBoost AUC: {auc_xgb:.4f}")
    
    # --- Ensemble ---
    p_ensemble = (p_lgbm + p_cat + p_xgb) / 3.0
    auc_ensemble = roc_auc_score(y_test, p_ensemble)
    print(f"\n🔮 KAHIN (v10) ENSEMBLE AUC: {auc_ensemble:.4f}")
    
    # --- Feature Importance ---
    print("\n📊 Feature Importance (Top 10):")
    importance = pd.DataFrame({
        'feature': features,
        'importance': lgbm.feature_importances_
    }).sort_values('importance', ascending=False).head(10)
    print(importance)
    
    # --- Save ---
    print("\n💾 Saving Model v10 (Kahin)...")
    joblib.dump(lgbm, 'model_v10_lgbm.pkl')
    joblib.dump(cat, 'model_v10_cat.pkl')
    joblib.dump(xgb_model, 'model_v10_xgb.pkl')
    joblib.dump(le_track, 'le_track_v10.pkl')
    joblib.dump(le_city, 'le_city_v10.pkl')
    
    print("✅ KAHIN (v10) is ready to see the future!")
    
    return auc_ensemble

if __name__ == "__main__":
    df, le_track, le_city = build_extended_features()
    train_model_v10(df, le_track, le_city)
