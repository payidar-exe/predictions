
import sqlite3
import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
import sys
import os

# Add current directory to path to import production_engine
sys.path.append(os.getcwd())

# Import helpers from production_engine
# We need to make sure production_engine doesn't run main() on import.
# It has if __name__ == "__main__", so it's safe.
from production_engine import (
    get_historical_stats_v10,
    compute_galop_features,
    golden_ratio_score, fibonacci_resonance, prime_harmony,
    cosmic_wave, chaos_attractor, numerology_score, moon_phase,
    PHI, FIBONACCI
)
import math

DB_NAME = "tjk_races.db"

def get_past_dates(days=15):
    conn = sqlite3.connect(DB_NAME)
    # Get all distinct dates
    dates = pd.read_sql_query("SELECT DISTINCT date FROM races", conn)['date'].tolist()
    conn.close()
    
    valid_dates = []
    today = datetime.now()
    cutoff = today - timedelta(days=days)
    
    for d_str in dates:
        try:
            # Try both formats
            if '/' in d_str:
                d = datetime.strptime(d_str, '%d/%m/%Y')
            else:
                d = datetime.strptime(d_str, '%Y-%m-%d')
                
            if cutoff <= d < today: # Past 15 days, excluding today (results might not be in yet or it is today)
                valid_dates.append((d, d_str))
        except:
            pass
            
    valid_dates.sort(key=lambda x: x[0])
    return [x[1] for x in valid_dates]

def load_day_data(date_str):
    conn = sqlite3.connect(DB_NAME)
    query = """
        SELECT 
            r.id as race_id, r.city, r.track_type, r.distance, r.prize, r.race_no,
            res.horse_name, res.jockey, res.trainer, res.owner,
            res.rank, res.weight, res.hp,
            r.date
        FROM results res
        JOIN races r ON res.race_id = r.id
        WHERE r.date = ?
    """
    df = pd.read_sql_query(query, conn, params=(date_str,))
    
    # Also fetch ALL galops for these horses to pass to compute logic
    if not df.empty:
        horse_names = tuple(df['horse_name'].dropna().unique().tolist())
        if horse_names:
            # Construct placeholder string
            placeholders = ','.join(['?'] * len(horse_names))
            g_query = f"SELECT * FROM gallops WHERE horse_name IN ({placeholders})"
            gallops_df = pd.read_sql_query(g_query, conn, params=horse_names)
        else:
            gallops_df = pd.DataFrame()
    else:
        gallops_df = pd.DataFrame()
        
    conn.close()
    return df, gallops_df

def run_backtest():
    dates = get_past_dates(15)
    print(f"🔄 Backtesting on {len(dates)} days: {dates}")
    
    # Load Models
    try:
        lgbm = joblib.load('model_v10_lgbm.pkl')
        cat = joblib.load('model_v10_cat.pkl')
        xgb_model = joblib.load('model_v10_xgb.pkl')
        le_track = joblib.load('le_track_v10.pkl')
        le_city = joblib.load('le_city_v10.pkl')
    except Exception as e:
        print(f"❌ Failed to load models: {e}")
        return

    # Metrics
    total_races = 0
    correct_win = 0
    correct_show = 0 # Top 3
    total_bet = 0
    total_return = 0
    
    results_log = []

    for d_str in dates:
        print(f"\n📅 Processing {d_str}...")
        df, gallops_df = load_day_data(d_str)
        
        if df.empty:
            print("   ⚠️ No data.")
            continue
            
        # --- FEATURE ENGINEERING (Replicating prepare_v10_predictions) ---
        
        # 1. Basic Transforms
        def safe_transform(le, col):
            known = set(le.classes_)
            return col.apply(lambda x: le.transform([str(x)])[0] if str(x) in known else 0)

        df['track_encoded'] = safe_transform(le_track, df['track_type'])
        df['city_encoded'] = safe_transform(le_city, df['city'])
        df['hp'] = pd.to_numeric(df['hp'], errors='coerce').fillna(0)
        df['weight'] = pd.to_numeric(df['weight'], errors='coerce').fillna(55)
        df['distance'] = pd.to_numeric(df['distance'], errors='coerce').fillna(1400)
        
        # 2. Historical Stats
        m5_vec, imp_vec, com_vec, trk_vec, own_vec, trn_vec = [], [], [], [], [], []
        q_gold, q_fib, q_pri, q_cos, q_chaos, q_num, q_moon = [], [], [], [], [], [], []
        
        conn = sqlite3.connect(DB_NAME)
        for idx, row in df.iterrows():
            m5, imp, com, trk, own, trn = get_historical_stats_v10(
                row['horse_name'], row['jockey'], row['track_type'], 
                row.get('trainer'), row.get('owner'), d_str,
                conn=conn
            )
            m5_vec.append(m5); imp_vec.append(imp); com_vec.append(com)
            trk_vec.append(trk); own_vec.append(own); trn_vec.append(trn)
            
            # Quantum
            race_n = row['race_no'] if row['race_no'] else 1
            h_ord = ord(row['horse_name'][0]) % 10 if row['horse_name'] else 1
            
            q_gold.append(golden_ratio_score(m5))
            q_fib.append(fibonacci_resonance(race_n, h_ord))
            q_pri.append(prime_harmony(row['hp'], row['weight']))
            q_cos.append(cosmic_wave(d_str, race_n))
            q_chaos.append(chaos_attractor(m5, com, trk))
            q_num.append(numerology_score(row['horse_name']))
            q_moon.append(moon_phase(d_str))
        conn.close()
        
        df['momentum_5'] = m5_vec
        df['improvement_trend'] = imp_vec
        df['combo_win_rate'] = com_vec
        df['track_win_rate'] = trk_vec
        df['owner_win_rate'] = own_vec
        df['trainer_win_rate_ext'] = 0.1 
        df['trainer_recent_form'] = trn_vec
        
        df['quantum_golden'] = q_gold
        df['quantum_fibonacci'] = q_fib
        df['quantum_prime'] = q_pri
        df['quantum_cosmic'] = q_cos
        df['quantum_chaos'] = q_chaos
        df['quantum_numerology'] = q_num
        df['quantum_moon'] = q_moon

        df['quantum_field'] = (
            df['quantum_golden'] * PHI +
            df['quantum_fibonacci'] * (FIBONACCI[7] / 21) +
            df['quantum_prime'] * math.pi +
            df['quantum_cosmic'] * math.e +
            df['quantum_chaos'] * 2.71828 +
            df['quantum_numerology'] * 7 / 9 +
            df['quantum_moon'] * 0.5
        ) / 10.0
        
        # 3. GALOP Features
        # Using the DB-loaded gallops_df
        df = compute_galop_features(df, gallops_df, d_str)
        
        # 4. Predict
        features = ['distance', 'weight', 'track_encoded', 'city_encoded', 'hp',
                    'momentum_5', 'improvement_trend', 'owner_win_rate', 
                    'trainer_win_rate_ext', 'trainer_recent_form', 'combo_win_rate', 'track_win_rate',
                    'quantum_golden', 'quantum_fibonacci', 'quantum_prime',
                    'quantum_cosmic', 'quantum_chaos', 'quantum_numerology', 
                    'quantum_moon', 'quantum_field',
                    'days_since_galop', 'galop_speed']
        
        for f in features:
            if f not in df.columns: df[f] = 0
            
        X = df[features].astype(float)
        p1 = lgbm.predict_proba(X)[:, 1]
        p2 = cat.predict_proba(X)[:, 1]
        p3 = xgb_model.predict_proba(X)[:, 1]
        df['ai_prob_base'] = (p1 + p2 + p3) / 3.0
        
        # Galop Boost
        galop_boost = (df['galop_score'] - 0.5) * 0.2
        df['ai_prob'] = (df['ai_prob_base'] + galop_boost).clip(0.01, 0.99)
        
        # --- EVALUATION ---
        # Group by race
        for (city, race_no), gdf in df.groupby(['city', 'race_no']):
            if len(gdf) < 3: continue
            
            # Prediction: Top Horse by ai_prob
            top_horse = gdf.sort_values('ai_prob', ascending=False).iloc[0]
            
            # Actual Winner: Rank 1
            winner = gdf[gdf['rank'] == 1]
            if winner.empty: continue
            winner_name = winner.iloc[0]['horse_name']
            
            # Metrics
            total_races += 1
            total_bet += 1 # Mock unit bet
            
            is_win = (top_horse['horse_name'] == winner_name)
            
            # Check top 3
            top3 = gdf.sort_values('ai_prob', ascending=False).head(3)['horse_name'].tolist()
            is_show = (winner_name in top3)
            
            if is_win:
                correct_win += 1
                # Calculate return approx (Mock odds if not available, usually ~3.0 for fav)
                # We don't have historical odds easily available in 'results' table usually?
                # DB schema has 'prize'? Not odds.
                # Use a standard 2.50 for favorite win for ROI calc simulation
                total_return += 2.5 
            
            if is_show:
                correct_show += 1
            
            results_log.append({
                'date': d_str,
                'city': city,
                'race': race_no,
                'pred': top_horse['horse_name'],
                'prob': f"{top_horse['ai_prob']:.2f}",
                'actual': winner_name,
                'success': "✅" if is_win else ("🆗" if is_show else "❌")
            })

    # Report
    print("\n" + "="*60)
    print("📊 BACKTEST REPORT (LAST 15 DAYS)")
    print("="*60)
    print(f"Total Races: {total_races}")
    print(f"Win Accuracy (Top 1): {correct_win}/{total_races} ({correct_win/total_races*100:.1f}%)")
    print(f"Show Accuracy (Top 3): {correct_show}/{total_races} ({correct_show/total_races*100:.1f}%)")
    print("-" * 60)
    
    # Detailed Log (Last 10)
    print("Recent Predictions:")
    for log in results_log[-10:]:
        print(f"{log['date']} {log['city']} R{log['race']}: Pred: {log['pred']} ({log['prob']}) | Actual: {log['actual']} | {log['success']}")

if __name__ == "__main__":
    run_backtest()
