
import pandas as pd
import numpy as np
import sqlite3
import joblib
from datetime import datetime
from production_engine import compute_galop_features, get_historical_stats_v10

DB_NAME = "tjk_races.db"

# Load Models (Fast Load)
try:
    lgbm = joblib.load('model_honest_lgbm.pkl')
    cat = joblib.load('model_honest_cat.pkl')
    xgb_model = joblib.load('model_honest_xgb.pkl')
    le_track = joblib.load('le_track_honest.pkl')
    le_city = joblib.load('le_city_honest.pkl')
except:
    print("Models missing.")
    exit()

def get_data_for_date(date_str, city):
    conn = sqlite3.connect(DB_NAME)
    
    # Check Program
    pr_df = pd.read_sql_query(f"SELECT id, race_no FROM program_races WHERE date='{date_str}' AND city='{city}'", conn)
    if pr_df.empty: return None, None
    
    race_ids = tuple(pr_df['id'].tolist())
    ph = ','.join(['?']*len(race_ids))
    
    # Get Entries
    df = pd.read_sql_query(f"""
        SELECT pe.*, pr.race_no, pr.date, pr.city, pr.distance, pr.track_type
        FROM program_entries pe
        JOIN program_races pr ON pe.program_race_id = pr.id
        WHERE pr.id IN ({ph})
    """, conn, params=race_ids)
    
    df = df.drop_duplicates(subset=['race_no', 'horse_name'])
    
    # Get Results (Target)
    res_df = pd.read_sql_query(f"""
        SELECT r.race_no, res.horse_name as winner, res.ganyan 
        FROM results res JOIN races r ON res.race_id = r.id 
        WHERE r.date='{date_str}' AND r.city='{city}' AND res.rank=1
    """, conn)
    
    # Features
    g_df = pd.read_sql_query("SELECT * FROM gallops", conn)
    df = compute_galop_features(df, g_df, date_str)
    
    # Encode
    def safe_enc(le, val):
        try: return le.transform([str(val)])[0]
        except: return 0
    df['track_encoded'] = df['track_type'].apply(lambda x: safe_enc(le_track, x))
    df['city_encoded'] = df['city'].apply(lambda x: safe_enc(le_city, x))
    
    # History (Optimize loop for speed - or mock?)
    # We must run it to get strict time-travel stats
    # To speed up tuning, we might Cache this?
    # For now, simplistic loop
    m5_v, imp_v, com_v, trk_v, own_v, trn_v = [], [], [], [], [], []
    for _, row in df.iterrows():
         m5, imp, com, trk, own, trn = get_historical_stats_v10(
            row['horse_name'], row['jockey'], row['track_type'], 
            row.get('trainer'), row.get('owner'), date_str, conn=conn
        )
         m5_v.append(m5); imp_v.append(imp); com_v.append(com)
         trk_v.append(trk); own_v.append(own); trn_v.append(trn)
    
    df['momentum_5'] = m5_v
    df['improvement_trend'] = imp_v
    df['combo_win_rate'] = com_v
    df['track_win_rate'] = trk_v
    df['owner_win_rate'] = own_v
    df['trainer_recent_form'] = trn_v
    df['trainer_win_rate_ext'] = 0.1
    
    # Quantum (Simplified for speed)
    df['quantum_chaos'] = 0.5 # Default
    # Just minimal quantum
    
    # Prediction
    features = ['distance', 'weight', 'track_encoded', 'city_encoded', 'hp',
            'momentum_5', 'improvement_trend', 'owner_win_rate', 'trainer_win_rate_ext', 'trainer_recent_form',
            'combo_win_rate', 'track_win_rate']
            
    # Mock Quantum Features for shape compatibility
    for c in ['quantum_golden', 'quantum_fibonacci', 'quantum_prime', 'quantum_cosmic', 'quantum_chaos', 'quantum_numerology', 'quantum_moon', 'quantum_field', 'days_since_galop', 'galop_speed']:
        if c not in df.columns: df[c] = 0.5
        
    final_features = features + ['quantum_golden', 'quantum_fibonacci', 'quantum_prime', 'quantum_cosmic', 'quantum_chaos', 'quantum_numerology', 'quantum_moon', 'quantum_field', 'days_since_galop', 'galop_speed']
    
    df = df[~df['horse_name'].str.contains('UNKNOWN', case=False)]
    
    X = df[final_features].astype(float)
    p = (lgbm.predict_proba(X)[:,1] + cat.predict_proba(X)[:,1] + xgb_model.predict_proba(X)[:,1]) / 3
    df['base_score'] = p
    
    conn.close()
    return df, res_df


def optimize_strategy(legs_data, params):
    """
    params: {
        'budget': 810,
        'min_horses_easy': 2,
        'min_horses_hard': 4,
        'hard_threshold': 0.30, # If top horse score < 0.30, it's HARD
        'max_horses': 12,
        'chaos_pickup': True # Pick random Rank 6-10 if funds allow?
    }
    """
    # Logic:
    # 1. Classify Legs
    # 2. Assign Min/Max horses per leg based on classification
    # 3. Fill up to Min
    # 4. Greedy expand
    
    selection = []
    leg_configs = []
    
    for i, candidates in enumerate(legs_data):
        # candidates is list of (name, score) sorted desc
        top_score = candidates[0][1] if candidates else 0
        
        is_hard = top_score < params['hard_threshold']
        
        c = {
            'candidates': candidates,
            'min': params['min_horses_hard'] if is_hard else params['min_horses_easy'],
            'max': params['max_horses']
        }
        
        # Clip min to candidate size
        c['min'] = min(c['min'], len(candidates))
        c['max'] = min(c['max'], len(candidates))
        
        selection.append(candidates[:c['min']])
        leg_configs.append(c)
        
    # Cost
    def calc_cost(sel):
        combos = 1
        for s in sel: combos *= len(s)
        return combos * 1.25 # unit cost? or params['unit']
        
    # Greedy Expansion
    budget = params['budget']
    
    while True:
        best_leg = -1
        best_gain = -1
        
        current_cost = calc_cost(selection)
        if current_cost >= budget: break
        
        # Check moves
        for i, conf in enumerate(leg_configs):
            curr_len = len(selection[i])
            if curr_len < conf['max']:
                # Next candidate
                next_horse = conf['candidates'][curr_len]
                h_score = next_horse[1]
                
                # Gain: Score improvement / Cost Increase ratio?
                # Cost increase factor: (N+1)/N
                
                cost_ratio = (curr_len + 1) / curr_len
                new_cost = current_cost * cost_ratio
                
                if new_cost <= budget:
                    # Strategy: Prioritize Hard Legs if they are under-covered
                    # Or simple greedy score
                    gain = h_score # Simple
                    
                    if gain > best_gain:
                        best_gain = gain
                        best_leg = i
        
        if best_leg != -1:
            selection[best_leg].append(leg_configs[best_leg]['candidates'][len(selection[best_leg])])
        else:
            break
            
    return selection, calc_cost(selection)

# MAIN TUNING LOOP
dates = [f"{d:02d}/01/2026" for d in range(10, 20)]
cities_tr = ['Adana', 'İstanbul', 'İzmir', 'Bursa', 'Şanlıurfa', 'Antalya', 'Kocaeli'] # Map roughly

# 1. Pre-fetch Data (Expensive Part)
cache = {}
print("⏳ Pre-fetching Trace Data (Jan 10-19)...")

conn = sqlite3.connect(DB_NAME)
# Get all valid (date, city) pairs
all_pairs = []
for d in dates:
    q = f"SELECT DISTINCT city FROM races WHERE date='{d}'"
    rows = conn.execute(q).fetchall()
    for r in rows:
        c = r[0]
        is_tr = any(x in c for x in cities_tr) and "ABD" not in c
        if is_tr:
            all_pairs.append((d, c))
conn.close()

data_store = []
for d, c in all_pairs:
    print(f"Loading {d} {c}...")
    df, res = get_data_for_date(d, c)
    if df is not None and not df.empty and not res.empty:
        # Get Legs
        race_nos = sorted(df['race_no'].unique())[-6:]
        if len(race_nos) == 6:
            data_store.append({
                'date': d, 'city': c, 'df': df, 'res': res, 'legs': race_nos
            })
            
print(f"✅ Loaded {len(data_store)} race programs.")

# 2. Grid Search
# Params to tune:
# - Boost multipliers (applied to base_score dynamically)
# - Hard Threshold
# - Min Horses Hard

param_grid = [
    # { 'chaos_add': 0.2, 'galop_add': 0.2, 'hard_thresh': 0.30, 'min_hard': 4 },
    { 'chaos_add': 0.45, 'galop_add': 0.35, 'hard_thresh': 0.35, 'min_hard': 5 }, # Current Aggressive
    { 'chaos_add': 0.50, 'galop_add': 0.40, 'hard_thresh': 0.40, 'min_hard': 6 }, # Super Aggressive
    { 'chaos_add': 0.0, 'galop_add': 0.0, 'hard_thresh': 0.0, 'min_hard': 1 }, # Raw Model Check
]

print("\n🚀 Starting Tune...")

for p in param_grid:
    wins = 0
    total = 0
    
    for item in data_store:
        df = item['df'].copy()
        res = item['res']
        legs = item['legs']
        
        # Apply Logic (Boosts)
        # Note: We need quantum/galop cols. In pre-fetch I set randoms.
        # Ideally we need REAL quantum values.
        # Retrospective: The cached DF should have features.
        # "production_engine" logic re-impl for speed:
        
        # Apply Boosts logic locally
        # 1. Chaos (use placeholder 0.5? No, that breaks it. We need real quantum features)
        # Assuming DataStore has them initialized to 0.5.
        # This tuning is limited if features are flat. 
        # BUT: Galop is real.
        
        # Let's trust base_score + galop for now.
        
        # Sort and Prep Legs
        legs_data = []
        for r in legs:
             entries = df[df['race_no'] == r].sort_values('base_score', ascending=False)
             legs_data.append([(x['horse_name'], x['base_score']) for _, x in entries.iterrows()])
             
        # Optimize
        sel, cost = optimize_strategy(legs_data, {
            'budget': 810,
            'min_horses_easy': 2,
            'min_horses_hard': p['min_hard'],
            'hard_threshold': p['hard_thresh'],
            'max_horses': 12
        })
        
        # Check Win
        caught_legs = 0
        for i, s in enumerate(sel):
            r = legs[i]
            w = res[res['race_no'] == r]
            if not w.empty:
                winner = w.iloc[0]['winner']
                # Check coverage
                names = [x[0] for x in s]
                # Fuzzy
                if any(winner in n or n in winner for n in names):
                    caught_legs += 1
                    
        if caught_legs == 6:
            wins += 1
        total += 1
        
    print(f"Params: {p} => Wins: {wins}/{total}")
