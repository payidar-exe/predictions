
import sqlite3
import pandas as pd
import json
import random
import sys
import os

# Import production engine components
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

def get_past_dates(days=7): # 7 days to get enough data
    conn = sqlite3.connect(DB_NAME)
    dates = pd.read_sql_query("SELECT DISTINCT date FROM races", conn)['date'].tolist()
    conn.close()
    
    from datetime import datetime
    valid_dates = []
    
    for d_str in dates:
        try:
            if '/' in d_str: d = datetime.strptime(d_str, '%d/%m/%Y')
            else: d = datetime.strptime(d_str, '%Y-%m-%d')
            valid_dates.append((d, d_str))
        except: pass
            
    valid_dates.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in valid_dates[:days]] # Last N days

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
    
    if not df.empty:
        horse_names = tuple(df['horse_name'].dropna().unique().tolist())
        if horse_names:
            placeholders = ','.join(['?'] * len(horse_names))
            g_query = f"SELECT * FROM gallops WHERE horse_name IN ({placeholders})"
            gallops_df = pd.read_sql_query(g_query, conn, params=horse_names)
        else:
            gallops_df = pd.DataFrame()
    else:
        gallops_df = pd.DataFrame()
        
    conn.close()
    return df, gallops_df

def generate_seed():
    dates = get_past_dates(5)
    
    # Load Models (Mock or Real - reusing real logic)
    import joblib
    try:
        lgbm = joblib.load('model_v10_lgbm.pkl')
        cat = joblib.load('model_v10_cat.pkl')
        xgb_model = joblib.load('model_v10_xgb.pkl')
        le_track = joblib.load('le_track_v10.pkl')
        le_city = joblib.load('le_city_v10.pkl')
    except:
        print("-- Error loading models")
        return

    print("-- Seed Data Generation calling...")
    print("DELETE FROM coupons;") # Clear old history
    
    for d_str in dates:
        df, gallops_df = load_day_data(d_str)
        if df.empty: continue
        
        # Format date for SQL (YYYY-MM-DD)
        try:
            if '/' in d_str: 
                parts = d_str.split('/')
                sql_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
            else: sql_date = d_str
        except: sql_date = d_str

        # --- PREDICT ---
        def safe_transform(le, col):
            known = set(le.classes_)
            return col.apply(lambda x: le.transform([str(x)])[0] if str(x) in known else 0)

        df['track_encoded'] = safe_transform(le_track, df['track_type'])
        df['city_encoded'] = safe_transform(le_city, df['city'])
        df['hp'] = pd.to_numeric(df['hp'], errors='coerce').fillna(0)
        df['weight'] = pd.to_numeric(df['weight'], errors='coerce').fillna(55)
        df['distance'] = pd.to_numeric(df['distance'], errors='coerce').fillna(1400)
        
        # Historical & Quantum
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
        
        df = compute_galop_features(df, gallops_df, d_str)
        
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
        
        galop_boost = (df['galop_score'] - 0.5) * 0.2
        df['ai_prob'] = (df['ai_prob_base'] + galop_boost).clip(0.01, 0.99)
        df['score'] = df['ai_prob'] * 1.0

        # --- COUPON GEN ---
        for city, cdf in df.groupby('city'):
            race_nos = sorted(cdf['race_no'].unique())
            if len(race_nos) < 6: continue
            
            legs = race_nos[-6:]
            legs_data = []
            
            # Optimization Data
            for r in legs:
                r_df = cdf[cdf['race_no'] == r].sort_values('score', ascending=False)
                legs_data.append([(h['horse_name'], h['score']) for _, h in r_df.iterrows()])
            
            selection, cost = optimize_coupon_logic(legs_data, 700.0)
            
            # Legs JSON Construction
            legs_json = []
            caught_count = 0
            
            leg_idx = 0
            for r in legs:
                race_res = cdf[cdf['race_no'] == r]
                winner = race_res[race_res['rank'] == 1]
                
                leg_status = "lost"
                actual_winner = "Bilinmiyor"
                
                if not winner.empty:
                    w_name = winner.iloc[0]['horse_name']
                    actual_winner = w_name
                    # Check selection
                    sel_names = [x[0] for x in selection[leg_idx]]
                    if w_name in sel_names:
                        leg_status = "won"
                        caught_count += 1
                
                # Construct Leg Object
                leg_obj = {
                    "leg_no": leg_idx + 1,
                    "leg_result": leg_status,
                    "horses": [{"horse_name": h[0]} for h in selection[leg_idx]],
                    "actual_winner": actual_winner
                }
                legs_json.append(leg_obj)
                leg_idx += 1
            
            is_win = (caught_count == 6)
            status = 'won' if is_win else 'lost'
            
            # Winning Amount Logic
            winning_amount = 0
            if is_win:
                # Randomize somewhat realistic payout based on city
                if city in ['İstanbul', 'Ankara', 'İzmir']:
                    winning_amount = random.randint(3000, 15000)
                else:
                    winning_amount = random.randint(8000, 35000) # Smaller tracks often give higher surprise payouts? Actually varies.
            
            # Escape strings
            title = f"{city} Kahin Analizi"
            subtitle = f"TUTAR: {cost:.2f} TL"
            
            legs_str = json.dumps(legs_json, ensure_ascii=False).replace("'", "''")
            
            sql = f"""
            INSERT INTO coupons (date, city, type, star_cost, title, subtitle, status, winning_amount, legs)
            VALUES ('{sql_date}', '{city}', 'premium', 50, '{title}', '{subtitle}', '{status}', {winning_amount}, '{legs_str}');
            """
            print(sql.strip())
            print("")

if __name__ == "__main__":
    generate_seed()
