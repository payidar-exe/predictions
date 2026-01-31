
import sqlite3
import pandas as pd
import joblib
import sys
import os
import json
from datetime import datetime
from production_engine import (
    get_historical_stats_v10,
    compute_galop_features,
    optimize_coupon_logic, # Using the Updated Smart Logic
    DB_NAME
)

# Load Models Once
try:
    lgbm = joblib.load('model_honest_lgbm.pkl')
    cat = joblib.load('model_honest_cat.pkl')
    xgb_model = joblib.load('model_honest_xgb.pkl')
    le_track = joblib.load('le_track_honest.pkl')
    le_city = joblib.load('le_city_honest.pkl')
    print("✅ Models loaded.")
except:
    print("❌ Models failed to load. Run inside project dir.")
    sys.exit(1)

def analyze_date(target_date):
    print(f"\n🔎 ANALYZING {target_date}...")
    conn = sqlite3.connect(DB_NAME)
    
    # Get Cities with Results
    q_cities = f"SELECT DISTINCT city FROM races WHERE date='{target_date}'"
    cities = [r[0] for r in conn.execute(q_cities).fetchall()]
    
    # Filter: User requested TR Only
    tr_cities = [c for c in cities if "ABD" not in c and "Fransa" not in c and "Afrika" not in c and "Birleşik Krallık" not in c and "İrlanda" not in c and "Avustralya" not in c]
    # tr_cities = cities # ALL CITIES
    
    analysis_report = []

    for city in tr_cities:
        print(f"  🏙️  {city}")
        
        try:
            # 1. Get Program Data for Prediction
            # Need program_entries. If we don't have program entries for past dates, we can't predict.
            # Check if program_races exist for this date
            pr_df = pd.read_sql_query(f"SELECT id, race_no FROM program_races WHERE date='{target_date}' AND city='{city}'", conn)
            
            if pr_df.empty:
                print("    ⚠️ No program data found. Cannot simulate model.")
                continue
                
            # Get Entries
            race_ids = tuple(pr_df['id'].tolist())
            placeholders = ','.join(['?']*len(race_ids))
            df = pd.read_sql_query(f"""
                SELECT pe.*, pr.race_no, pr.date, pr.city, pr.distance, pr.track_type
                FROM program_entries pe
                JOIN program_races pr ON pe.program_race_id = pr.id
                WHERE pr.id IN ({placeholders})
            """, conn, params=race_ids)
            
            # Deduplicate (Fix we just added)
            df = df.drop_duplicates(subset=['race_no', 'horse_name'])
            
            if df.empty:
                print("    ⚠️ Entries found but dataframe is empty after load.")
                continue
            
            # Feature Engineering (Simplified for speed but accurate)
            # ... (We reuse the logic from production_engine essentially)
            # Galops
            g_df = pd.read_sql_query("SELECT * FROM gallops", conn) # Load all, memory heavy but safe for script
            df = compute_galop_features(df, g_df, target_date)
            
            # Encode
            def safe_enc(le, val):
                try: return le.transform([str(val)])[0]
                except: return 0
            df['track_encoded'] = df['track_type'].apply(lambda x: safe_enc(le_track, x))
            df['city_encoded'] = df['city'].apply(lambda x: safe_enc(le_city, x))
            
            # Historical
            m5_v, imp_v, com_v, trk_v, own_v, trn_v = [], [], [], [], [], []
            q_vecs = {k:[] for k in ['gold','fib','pri','cos','chaos','num','moon']}
            
            # History Loop
            for _, row in df.iterrows():
                m5, imp, com, trk, own, trn = get_historical_stats_v10(
                    row['horse_name'], row['jockey'], row['track_type'], 
                    row.get('trainer'), row.get('owner'), target_date, conn=conn
                )
                m5_v.append(m5); imp_v.append(imp); com_v.append(com)
                trk_v.append(trk); own_v.append(own); trn_v.append(trn)
                
                 # Quantum
                rn = row['race_no'] or 1
                hn = row['horse_name'] or "X"
                from production_engine import golden_ratio_score, fibonacci_resonance, prime_harmony, cosmic_wave, chaos_attractor, numerology_score, moon_phase, PHI, FIBONACCI
                
                q_vecs['gold'].append(golden_ratio_score(m5))
                q_vecs['fib'].append(fibonacci_resonance(rn, ord(hn[0])%10))
                q_vecs['pri'].append(prime_harmony(float(row.get('hp',0) or 0), float(row.get('weight',55) or 55)))
                q_vecs['cos'].append(cosmic_wave(target_date, rn))
                q_vecs['chaos'].append(chaos_attractor(m5, com, trk))
                q_vecs['num'].append(numerology_score(hn))
                q_vecs['moon'].append(moon_phase(target_date))
                
            df['momentum_5'] = m5_v
            df['improvement_trend'] = imp_v
            df['combo_win_rate'] = com_v
            df['track_win_rate'] = trk_v
            df['owner_win_rate'] = own_v
            df['trainer_recent_form'] = trn_v
            df['trainer_win_rate_ext'] = 0.1 # Placeholder
            
            for k in q_vecs: df[f'quantum_{"golden" if k=="gold" else "fibonacci" if k=="fib" else "prime" if k=="pri" else "cosmic" if k=="cos" else "chaos" if k=="chaos" else "numerology" if k=="num" else "moon"}'] = q_vecs[k]
        
            
            # Zero Quantum (Not critical for basic model check, but used in train?) 
            # Actually Model V10 uses quantum. We should add them if V10.
            # honest model uses quantum? Let's check columns.
            # Assuming yes for "honest" which was v10.5.
            # Correct Feature Order (Must match training!)
            # From error: quantum cols come BEFORE galop features
            features = ['distance', 'weight', 'track_encoded', 'city_encoded', 'hp',
                'momentum_5', 'improvement_trend', 'owner_win_rate', 'trainer_win_rate_ext', 'trainer_recent_form',
                'combo_win_rate', 'track_win_rate']
                
            # Add quantum then galop
            mq_cols = ['quantum_golden', 'quantum_fibonacci', 'quantum_prime', 'quantum_cosmic', 'quantum_chaos', 'quantum_numerology', 'quantum_moon', 'quantum_field']
            galop_cols = ['days_since_galop', 'galop_speed']
            
            # Final Feature List
            final_features = features + mq_cols + galop_cols
            
            for f in final_features: 
                if f not in df.columns: df[f] = 0
            
            # Filter Unknowns
            df = df[~df['horse_name'].str.contains('UNKNOWN', case=False, na=False)]
            
            if df.empty:
                print("    ⚠️ All entries filtered out (Unknowns).")
                continue
                
            # Predict
            X = df[final_features].astype(float)
            
            if X.shape[0] == 0:
                 print("    ⚠️ X matrix empty.")
                 continue
                 
            p = (lgbm.predict_proba(X)[:,1] + cat.predict_proba(X)[:,1] + xgb_model.predict_proba(X)[:,1]) / 3
            df['score'] = (p + (df['galop_score']-0.5)*0.2).clip(0,1)
        
        except Exception as e:
            print(f"    ❌ Critical Analysis Error for {city}: {e}")
            continue
        
        # --- QUANTUM & SURPRISE BOOST (Aggressive - Best Tested) ---
        # 1. Chaos Boost
        mask_chaos = (df['score'] < 0.25) & (df['quantum_chaos'] > 0.70)
        df.loc[mask_chaos, 'score'] += (df.loc[mask_chaos, 'quantum_chaos'] * 0.45)
        
        # 2. Galop Boost
        mask_galop = (df['momentum_5'] < 0.55) & (df['galop_score'] > 0.70)
        df.loc[mask_galop, 'score'] += 0.35
        
        # 3. Jockey Boost
        mask_joc = (df['combo_win_rate'] > 0.20) & (df['score'] < 0.25)
        df.loc[mask_joc, 'score'] += 0.25
        
        df['score'] = df['score'].clip(0, 0.98)
        
        # 2. Get Actual Results
        res_df = pd.read_sql_query(f"""
            SELECT r.race_no, res.horse_name as winner, res.ganyan 
            FROM results res JOIN races r ON res.race_id = r.id 
            WHERE r.date='{target_date}' AND r.city='{city}' AND res.rank=1
        """, conn)
        
        # 3. Analyze Legs (Last 6)
        race_nos = sorted(df['race_no'].unique())
        legs = race_nos[-6:]
        legs_data = []
        
        print(f"    Legs: {legs}")
        
        for i, r in enumerate(legs):
            entries = df[df['race_no'] == r].sort_values('score', ascending=False).reset_index(drop=True)
            legs_data.append([(x['horse_name'], x['score']) for _, x in entries.iterrows()])
            
            # Find Winner Info
            w_row = res_df[res_df['race_no'] == r]
            if w_row.empty:
                print(f"      Leg {i+1} (R{r}): Result Pending")
                continue
                
            winner_name = w_row.iloc[0]['winner']
            ganyan = w_row.iloc[0]['ganyan']
            
            # Find Winner in Predictions
            try:
                rank = entries[entries['horse_name'] == winner_name].index[0] + 1
                score = entries[entries['horse_name'] == winner_name].iloc[0]['score']
            except:
                # Name mismatch? Fuzzy match?
                # Simple loose match
                matches = entries[entries['horse_name'].str.contains(winner_name[:5], case=False)]
                if not matches.empty:
                    rank = matches.index[0] + 1
                    score = matches.iloc[0]['score']
                    winner_name = matches.iloc[0]['horse_name'] # Correct it
                else:
                    rank = 99
                    score = 0.0
            
            field_size = len(entries)
            
            # Log
            status = "✅" if rank == 1 else "⚠️" if rank <= 3 else "❌"
            print(f"      Leg {i+1} (R{r}): {status} Winner: {winner_name:<15} (Gny: {ganyan}) | Rank: {rank}/{field_size} | Score: {score:.2f}")
            
            analysis_report.append({
                'date': target_date,
                'city': city,
                'leg': i+1,
                'winner': winner_name,
                'ganyan': ganyan,
                'model_rank': rank,
                'model_score': score,
                'field_size': field_size
            })
            
        # 4. Simulate Smart Coupon
        print("    🧠 Simulating Smart Coupon...")
        try:
            sel, cost = optimize_coupon_logic(legs_data, 750.0) # Use new logic
            caught = 0
            for i, s in enumerate(sel):
                r = legs[i]
                w_row = res_df[res_df['race_no'] == r]
                if w_row.empty: continue
                winner = w_row.iloc[0]['winner']
                
                # Check coverage
                # Must handle name mismatch
                covered = False
                for h in s:
                    if h[0] == winner or winner in h[0] or h[0] in winner:
                        covered = True
                        break
                
                if covered: caught += 1
                else:
                     print(f"      ❌ Missed Leg {i+1}: Winner {winner} not in {[h[0] for h in s]}")
                     # Deep Debug
                     try:
                        w_row_df = entries[entries['horse_name'].str.contains(winner[:5], case=False)]
                        if not w_row_df.empty:
                            wd = w_row_df.iloc[0]
                            print(f"         🔍 WHY? Score: {wd['score']:.2f} | Chaos: {wd['quantum_chaos']:.2f} | Galop: {wd['galop_score']:.2f} | Mom: {wd['momentum_5']:.2f} | Jock: {wd['combo_win_rate']:.2f}")
                     except: pass
            
            print(f"    🏷️  Cost: {cost:.2f} TL | Caught: {caught}/6")
            
            if city == "Şanlıurfa  (5. Y.G.)" and target_date == "19/01/2026":
                print("\n    🌟 WINNING COUPON DETAILS 🌟")
                for k, s in enumerate(sel):
                    names = [x[0] for x in s]
                    print(f"      Leg {k+1}: {', '.join(names)}")
                print("    " + "="*30)
                
        except Exception as e:
            print(f"    ❌ Optimization Error: {e}")

    conn.close()
    return analysis_report

if __name__ == "__main__":
    all_reports = []
    # Generate dates 10-19
    dates = [f"{d:02d}/01/2026" for d in range(10, 20)]
    
    for d in dates:
        rep = analyze_date(d)
        all_reports.extend(rep)
        
    # Summary
    print("\n📊 FORENSIC SUMMARY")
    print("-" * 60)
    df_rep = pd.DataFrame(all_reports)
    if not df_rep.empty:
        # 1. Model Accuracy
        top1 = len(df_rep[df_rep['model_rank'] == 1])
        top3 = len(df_rep[df_rep['model_rank'] <= 3])
        top5 = len(df_rep[df_rep['model_rank'] <= 5])
        total = len(df_rep)
        
        print(f"Total Races: {total}")
        print(f"Winner Ranked #1: {top1} ({top1/total:.1%})")
        print(f"Winner Ranked Top 3: {top3} ({top3/total:.1%})")
        print(f"Winner Ranked Top 5: {top5} ({top5/total:.1%})")
        
        print("\n❌ MISSES (Rank > 5):")
        misses = df_rep[df_rep['model_rank'] > 5]
        for _, row in misses.iterrows():
            print(f"  {row['date']} {row['city']} L{row['leg']}: {row['winner']} (Rank {row['model_rank']}/{row['field_size']}, Score {row['model_score']:.2f})")
    
