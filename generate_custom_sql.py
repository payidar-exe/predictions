
import sqlite3
import pandas as pd
import json
import sys
import os
import joblib
import numpy as np
import math

# Add path for scraper imports if needed
sys.path.append('.')

from production_engine import (
    prepare_v10_predictions, 
    calculate_chaos_heuristic, 
    optimize_coupon_logic, 
    DB_NAME
)

def generate_sql_for_date(date_str, output_file="seed_data_today.sql"):
    conn = sqlite3.connect(DB_NAME)
    
    # Get TJK Cities (Turkish only)
    # Filter cities containing "Y.G." which typically denotes TJK program cities in our scraper
    # Or just hardcode logic to include specific known TR cities if needed.
    # Scraper output showed: "İzmir (7. Y.G.)", "Antalya (6. Y.G.)"
    cities_query = "SELECT DISTINCT city FROM program_races WHERE date = ? AND city LIKE '%Y.G.%'"
    cities = pd.read_sql_query(cities_query, conn, params=(date_str,))
    
    sql_statements = []
    sql_statements.append(f"DELETE FROM coupons WHERE date = CURRENT_DATE;")
    sql_statements.append("INSERT INTO coupons (date, city, type, star_cost, title, subtitle, legs) VALUES")
    
    values_list = []
    
    for _, city_row in cities.iterrows():
        city_full = city_row['city']
        city_name = city_full.split('(')[0].strip() # "İzmir"
        
        print(f"Processing {city_full}...")
        
        # Load Program Data with details
        query = """
        SELECT pr.id as race_id, pr.city, pr.distance, pr.track_type, pr.date as race_date, 
               pr.race_no, pr.time as race_time, pr.race_type as race_info,
               pe.program_race_id, pe.program_no, pe.horse_name, pe.weight, pe.jockey, 
               pe.hp, pe.horse_id, pe.trainer, pe.owner, pe.last_6_races
        FROM program_entries pe
        JOIN program_races pr ON pe.program_race_id = pr.id
        WHERE pr.city = ? AND pr.date = ?
        """
        df = pd.read_sql_query(query, conn, params=(city_full, date_str))
        
        if df.empty:
            print(f"Skipping {city_name} - No data")
            continue
            
        # Run Predictions
        df = prepare_v10_predictions(df, date_str)
        if df is None: continue
        
        # Determine 6 Legs (Last 6 races)
        race_nos = sorted(df['race_no'].unique())
        if len(race_nos) < 6:
            print(f"Skipping {city_name} - Not enough races ({len(race_nos)})")
            continue
            
        legs = race_nos[-6:]
        
        # Calculate Chaos for metadata
        avg_field_size = len(df) / len(race_nos)
        chaos_score = calculate_chaos_heuristic(city_full, len(race_nos), avg_field_size)
        
        # --- OPTIMIZATION STEP ---
        # Prepare data for optimizer: list of lists of (name, score)
        # We need 'score' column. Let's calculate it as per production_engine
        
        # Define Strategy Weights (Standard Logic)
        w_prob = 100
        w_mom = 20
        w_combo = 10
        w_track = 10
        w_surprise = 10
        
        # Normalize/Fill missing columns if needed (engine usually does this but let's be safe)
        if 'momentum_5' not in df.columns: df['momentum_5'] = 0.5
        if 'combo_win_rate' not in df.columns: df['combo_win_rate'] = 0.1
        if 'track_win_rate' not in df.columns: df['track_win_rate'] = 0.1
        if 'quantum_field' not in df.columns: df['quantum_field'] = 0.5
        
        df['score'] = (df['ai_prob'] * w_prob * 0.01) + \
                      (df['momentum_5'] * w_mom * 0.01) + \
                      (df['combo_win_rate'] * w_combo * 0.01) + \
                      (df['track_win_rate'] * w_track * 0.01) + \
                      (df['quantum_field'] * w_surprise * 0.01)
                      
        cols = []
        for r in legs:
            r_df = df[df['race_no'] == r].sort_values('score', ascending=False)
            cols.append([(h['horse_name'], h['score']) for _, h in r_df.iterrows()])
            
        # Run Optimizer (Budget ~600 TL for premium feel)
        # Using balanced logic for good coverage
        selection, cost = optimize_coupon_logic(cols, 600.0) 
        
        # Flatten selection for easy lookup
        selected_map = {i: [x[0] for x in sel] for i, sel in enumerate(selection)}
        
        legs_json = []
        
        for i, race_no in enumerate(legs):
            race_df = df[df['race_no'] == race_no].sort_values('ai_prob', ascending=False)
            meta = race_df.iloc[0]
            
            # Filter for selected horses in this leg
            selected_names = selected_map[i]
            
            horses_json = []
            # Identify Banko: Horse with highest AI Prob > 0.35 or significant gap
            top_horse = race_df.iloc[0]
            is_strong_fav = top_horse['ai_prob'] > 0.30 
            
            # 1. Collect raw scores first to normalize
            race_selected = []
            for _, horse in race_df.iterrows():
                if horse['horse_name'] in selected_names:
                    raw = horse['ai_prob'] * 100
                    if horse['momentum_5'] > 0.6: raw += 10
                    if horse['track_win_rate'] > 0.3: raw += 5
                    race_selected.append(raw)
            
            # Avoid division by zero
            if not race_selected: min_raw, max_raw = 0, 1
            else: min_raw, max_raw = min(race_selected), max(race_selected)
            
            if min_raw == max_raw: max_raw += 1 # Safety
            
            # Sort race_df by program_no to try and deduce it if missing? 
            # Actually, let's keep sorted by score for processing, but handle program_no carefully.
            
            for rank_idx, (_, horse) in enumerate(race_df.iterrows()):
                if horse['horse_name'] not in selected_names:
                    continue
                    
                # Fix Program No: Use existing or Fallback
                p_no = int(horse['program_no'])
                if p_no == 0:
                    p_no = rank_idx + 1 # Fallback to 1-based index in the selected list
                    
                # AI Score Calculation (Normalized to 78-98 range for selected horses)
                # This guarantees visual variance between runners
                raw_score = horse['ai_prob'] * 100
                if horse['momentum_5'] > 0.6: raw_score += 10
                if horse['track_win_rate'] > 0.3: raw_score += 5
                
                # Normalize: (val - min) / (max - min)
                norm = (raw_score - min_raw) / (max_raw - min_raw)
                # Map 0.0-1.0 to 78-98
                ai_score = int(78 + (norm * 20))
                
                # AI Note Generation - Richer templates based on statistics
                note = ""
                
                # Momentum-based notes
                if horse['momentum_5'] > 0.8:
                    note += "Son koşularında müthiş bir çıkış yakaladı, formunun zirvesinde. "
                elif horse['momentum_5'] > 0.7:
                    note += "Form grafiği yukarı yönlü, kendinden emin. "
                elif horse['momentum_5'] > 0.6:
                    note += "Son yarışlarında istikrarlı performans sergiliyor. "
                elif horse['momentum_5'] > 0.5:
                    note += "Formu yeterli düzeyde, sürpriz yapabilir. "
                
                # Track affinity notes
                if horse['track_win_rate'] > 0.5:
                    note += "Bu pist ve mesafe kombinasyonunda ezici üstünlüğü var. "
                elif horse['track_win_rate'] > 0.35:
                    note += "Kum/sentetik pistlerde güçlü istatistiklere sahip. "
                elif horse['track_win_rate'] > 0.25:
                    note += "Bu mesafeyi seviyor, rahat koşar. "
                
                # Combo notes (trainer/jockey)
                if horse.get('combo_win_rate', 0) > 0.3:
                    note += "Jokey-antrenör ikilisi birlikte çok başarılı. "
                
                # Probability-based general notes
                if horse['ai_prob'] > 0.35:
                    note += "Yapay zeka analizinde açık favori. "
                elif horse['ai_prob'] > 0.25:
                    note += "Güçlü aday, kuponu taşıyabilir. "
                
                # Keep note concise
                note = note.strip()[:150] if note else ""
                
                is_leg_banko = (len(selected_names) == 1) # Re-evaluate banko for this leg
                if is_leg_banko:
                    ai_score = 99 # Banko always gets Max score
                    note = f"🎯 BANKO TAHMİNİ: {note}" if note else "🎯 Yapay zekanın tek favorisi, kaçırılmaz fırsat!"
                
                horses_json.append({
                    "program_no": p_no,
                    "horse_name": horse['horse_name'],
                    "jockey_name": horse['jockey'],
                    "ai_score": ai_score,
                    "is_banko": is_leg_banko,
                    "ai_note": note
                })
            
            # Sort by program number for tidiness? Or Score? 
            # Usually program number is easier to read for coupons.
            # If program_no is 0, sort by ai_score desc
            horses_json.sort(key=lambda x: (x['program_no'] if x['program_no'] > 0 else 999, -x['ai_score']))
            
            legs_json.append({
                "leg_no": i + 1,
                "race_time": meta['race_time'] or "00:00",
                "race_info": meta['race_info'] or "Koşu",
                "distance": f"{int(float(meta['distance']))}m {meta['track_type']}",
                "field_size": len(race_df), # Original field size
                "horses": horses_json
            })
            
        # SQL Values
        # Escape single quotes in JSON
        json_str = json.dumps(legs_json, ensure_ascii=False).replace("'", "''")
        
        # Dynamic Pricing / Title
        title = f"{city_name} Kahin Analizi"
        subtitle = f"TUTAR: {cost:.2f} TL"
        star_cost = 50
        
        values_list.append(f"  (CURRENT_DATE, '{city_name}', 'premium', {star_cost}, '{title}', '{subtitle}', '{json_str}'::jsonb)")
        
    conn.close()
    
    if not values_list:
        print("No valid predictions generated.")
        return

    full_sql = "\n".join(sql_statements) + "\n" + ",\n".join(values_list) + ";"
    
    with open(output_file, "w") as f:
        f.write(full_sql)
        
    print(f"✅ Generated {output_file}")

if __name__ == "__main__":
    generate_sql_for_date("15/01/2026")
