
import sqlite3
import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime
import sys
import os

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
import math

DB_NAME = "tjk_races.db"

def get_real_test_dates(start_date):
    """Get race dates strictly AFTER cutoff"""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT DISTINCT date FROM races", conn)
    conn.close()
    
    valid = []
    cutoff = datetime.strptime(start_date, '%Y-%m-%d')
    for d_str in df['date']:
        try:
            if '/' in d_str: d = datetime.strptime(d_str, '%d/%m/%Y')
            else: d = datetime.strptime(d_str, '%Y-%m-%d')
            if d >= cutoff: valid.append((d, d_str))
        except: pass
    valid.sort(key=lambda x: x[0])
    return [x[1] for x in valid]

def run_real_backtest(dates=None, cutoff_iso=None, target_city=None):
    print("\n🔍 KAHIN BACKTEST RUNNER")
    if dates:
        print(f"   Testing Special Dates: {dates}")
    elif cutoff_iso:
        dates = get_real_test_dates(cutoff_iso)
        print(f"   Testing dates >= {cutoff_iso}")
    
    if target_city:
        print(f"   Target City: {target_city}")
        
    print("="*60)
    
    # Load Models
    try:
        # Try Loading Honest Models first, else Fallback
        model_prefix = 'model_honest'
        if not os.path.exists('model_honest_lgbm.pkl'): model_prefix = 'model_v10'
        
        lgbm = joblib.load(f'{model_prefix}_lgbm.pkl')
        cat = joblib.load(f'{model_prefix}_cat.pkl')
        xgb_model = joblib.load(f'{model_prefix}_xgb.pkl')
        le_track = joblib.load(f'le_track_{model_prefix.split("_")[1]}.pkl') # track_honest or track_v10
        le_city = joblib.load(f'le_city_{model_prefix.split("_")[1]}.pkl')
        print(f"✅ Loaded {model_prefix} models.")
    except Exception as e:
        print(f"❌ Failed to load models: {e}")
        return

    total_coupons = 0
    won_coupons = 0
    total_cost = 0
    
    for d_str in dates:
        # Load Day Data
        conn = sqlite3.connect(DB_NAME)
        query = f"SELECT * FROM races r JOIN results res ON r.id=res.race_id WHERE r.date='{d_str}'"
        df = pd.read_sql_query(query, conn)
        
        if target_city:
            df = df[df['city'].str.contains(target_city, case=False, na=False)]
            
        # Determine Galops (using simple logic from coupon_backtest)
        horse_names = tuple(df['horse_name'].dropna().unique().tolist())
        if horse_names:
            placeholders = ','.join(['?'] * len(horse_names))
            g_df = pd.read_sql_query(f"SELECT * FROM gallops WHERE horse_name IN ({placeholders})", conn, params=horse_names)
        else: g_df = pd.DataFrame()
        conn.close()
        
        if df.empty: continue
        
        # --- PREDICT (Feature Eng) ---
        def safe_enc(le, val):
            try: return le.transform([str(val)])[0]
            except: return 0
            
        df['track_encoded'] = df['track_type'].apply(lambda x: safe_enc(le_track, x))
        df['city_encoded'] = df['city'].apply(lambda x: safe_enc(le_city, x))
        
        # Re-calc historicals using SHARED CONN
        conn = sqlite3.connect(DB_NAME)
        m5_vec = []; imp_vec = []; com_vec = []; trk_vec = []; own_vec = []; trn_vec = []
        q_vecs = {k:[] for k in ['gold','fib','pri','cos','chaos','num','moon']}
        
        for idx, row in df.iterrows():
            m5, imp, com, trk, own, trn = get_historical_stats_v10(
                row['horse_name'], row['jockey'], row['track_type'], 
                row.get('trainer'), row.get('owner'), d_str, conn=conn
            )
            m5_vec.append(m5); imp_vec.append(imp); com_vec.append(com); trk_vec.append(trk); own_vec.append(own); trn_vec.append(trn)
            
            # Quantum
            rn = row['race_no'] or 1
            hn = row['horse_name'] or "X"
            q_vecs['gold'].append(golden_ratio_score(m5))
            q_vecs['fib'].append(fibonacci_resonance(rn, ord(hn[0])%10))
            q_vecs['pri'].append(prime_harmony(float(row['hp'] or 0), float(row['weight'] or 55)))
            q_vecs['cos'].append(cosmic_wave(d_str, rn))
            q_vecs['chaos'].append(chaos_attractor(m5, com, trk))
            q_vecs['num'].append(numerology_score(hn))
            q_vecs['moon'].append(moon_phase(d_str))
            
        conn.close()
        
        df['momentum_5'] = m5_vec; df['improvement_trend'] = imp_vec
        df['combo_win_rate'] = com_vec; df['track_win_rate'] = trk_vec
        df['owner_win_rate'] = own_vec; df['trainer_recent_form'] = trn_vec
        df['trainer_win_rate_ext'] = 0.1
        
        for k in q_vecs: df[f'quantum_{"golden" if k=="gold" else "fibonacci" if k=="fib" else "prime" if k=="pri" else "cosmic" if k=="cos" else "chaos" if k=="chaos" else "numerology" if k=="num" else "moon"}'] = q_vecs[k]
        
        df['quantum_field'] = (df['quantum_golden']*PHI + df['quantum_fibonacci']*(FIBONACCI[7]/21) + df['quantum_prime']*math.pi + df['quantum_cosmic']*math.e + df['quantum_chaos']*2.718 + df['quantum_numerology']*7/9 + df['quantum_moon']*0.5)/10
        
        df = compute_galop_features(df, g_df, d_str)
        
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
        
        # --- COUPON ---
        for city, cdf in df.groupby('city'):
            races = sorted(cdf['race_no'].unique())
            if len(races) < 6: continue
            
            # Take last 6 races (Altılı Ganyan)
            legs = races[-6:]
            legs_data = []
            
            for r in legs:
                r_df = cdf[cdf['race_no'] == r].sort_values('score', ascending=False)
                legs_data.append([(x['horse_name'], x['score']) for _, x in r_df.iterrows()])
            
            sel, cost = optimize_coupon_logic(legs_data, 700.0)
            
            # Check Win
            caught = 0
            missed_legs = []
            
            leg_idx = 0
            for r in legs:
                res = cdf[cdf['race_no'] == r]
                winner = res[res['rank'] == 1]['horse_name'].values
                w_name = winner[0] if len(winner)>0 else "Unknown"
                
                my_horses = [x[0] for x in sel[leg_idx]]
                if w_name in my_horses: caught += 1
                else: missed_legs.append(f"L{leg_idx+1}({w_name})")
                leg_idx += 1
                
            is_win = (caught == 6)
            total_coupons += 1
            if is_win: won_coupons += 1
            total_cost += cost
            
            status_icon = "✅" if is_win else "❌"
            print(f"{d_str} | {city:20} | {cost:6.2f} TL | {status_icon} {caught}/6 | Missed: {', '.join(missed_legs)}")

    print("="*60)
    print(f"TOTAL RESULT:")
    print(f"Coupons: {total_coupons}")
    print(f"Won: {won_coupons}")
    ratio = won_coupons/total_coupons*100 if total_coupons > 0 else 0
    print(f"Win Rate: {ratio:.1f}%")
    print(f"Total Cost: {total_cost:.2f} TL")
    
if __name__ == "__main__":
    # ANTALYA CHECK
    specific_dates = ['01/01/2026', '02/01/2026', '06/01/2026', '08/01/2026']
    run_real_backtest(dates=specific_dates, target_city="Antalya")
