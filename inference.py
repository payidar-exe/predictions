import sqlite3
import pandas as pd
import joblib
import argparse
import time
from datetime import datetime

# DB Connection
DB_NAME = "tjk_races.db"

def load_program(city, date_str):
    conn = sqlite3.connect(DB_NAME)
    query = """
    SELECT 
        pr.id as race_id, pr.city, pr.distance, pr.track_type, pr.date as race_date,
        pe.program_race_id, pe.program_no, pe.horse_name, pe.weight, pe.jockey, pe.trainer,
        pe.last_6_races, pe.hp, pe.gallop_info
    FROM program_entries pe
    JOIN program_races pr ON pe.program_race_id = pr.id
    WHERE pr.city LIKE ? AND pr.date = ?
    """
    df = pd.read_sql_query(query, conn, params=(f'%{city}%', date_str))
    conn.close()
    return df

def parse_gallop_features(df):
    # Calculate days_since_gallop and gallop_speed
    speeds = []
    days_list = []
    
    for idx, row in df.iterrows():
        g_info = str(row.get('gallop_info', ''))
        r_date_str = str(row.get('race_date', ''))
        
        speed = 0.0
        days = 999
        
        if g_info and "QUEUE" not in g_info and "N/A" not in g_info and len(g_info) > 10:
            try:
                # "10/01/2026 - 800m: 0.54.20"
                parts = g_info.split('-')
                if len(parts) >= 2:
                    g_date_str = parts[0].strip()
                    metrics = parts[1].strip() # 800m: 0.54.20
                    
                    # Date
                    g_date = pd.to_datetime(g_date_str, dayfirst=True)
                    r_date = pd.to_datetime(r_date_str, dayfirst=True)
                    days = (r_date - g_date).days
                    
                    # Speed
                    if ':' in metrics:
                        m_parts = metrics.split(':')
                        dist_val = float(m_parts[0].replace('m','').strip())
                        time_val = m_parts[1].strip()
                        
                        duration = 0.0
                        t_parts = time_val.replace(':', '.').split('.')
                        if len(t_parts) == 3: 
                            duration = float(t_parts[0])*60 + float(t_parts[1]) + float(t_parts[2])/100
                        elif len(t_parts) == 2:
                            duration = float(t_parts[0]) + float(t_parts[1])/100
                        else:
                            duration = float(time_val)
                            
                        if duration > 0:
                            speed = dist_val / duration
            except:
                pass
        
        speeds.append(speed)
        days_list.append(days)
        
    df['gallop_speed'] = speeds
    df['days_since_gallop'] = days_list
    return df

def get_latest_stats(program_df):
    """
    Looks up the most recent stats for Jockeys/Trainers/Horses from the history dataset.
    """
    print("Loading historical stats knowledge base...")
    try:
        history_df = pd.read_csv('features_dataset.csv')
        
        # We want the LAST known stat for each entity.
        # Group by entity and take the last row (assuming sorted by date)
        jockey_stats = history_df.groupby('jockey')[['jockey_win_rate', 'jockey_races']].last().to_dict('index')
        trainer_stats = history_df.groupby('trainer')[['trainer_win_rate', 'trainer_races']].last().to_dict('index')
        horse_stats = history_df.groupby('horse_name')[['horse_win_rate', 'horse_races']].last().to_dict('index')
        
        avg_j_rate = history_df['jockey_win_rate'].mean()
        avg_t_rate = history_df['trainer_win_rate'].mean()
    except:
        # Fallback if file missing (first run)
        jockey_stats, trainer_stats, horse_stats = {}, {}, {}
        avg_j_rate, avg_t_rate = 0.1, 0.1

    def get_stat(source_dict, key, field, default=0):
        if key in source_dict:
            return source_dict[key][field]
        return default

    program_df['jockey_win_rate'] = program_df['jockey'].apply(lambda x: get_stat(jockey_stats, x, 'jockey_win_rate', avg_j_rate))
    program_df['jockey_races'] = program_df['jockey'].apply(lambda x: get_stat(jockey_stats, x, 'jockey_races', 0))
    
    program_df['trainer_win_rate'] = program_df['trainer'].apply(lambda x: get_stat(trainer_stats, x, 'trainer_win_rate', avg_t_rate))
    program_df['trainer_races'] = program_df['trainer'].apply(lambda x: get_stat(trainer_stats, x, 'trainer_races', 0))
    
    program_df['horse_win_rate'] = program_df['horse_name'].apply(lambda x: get_stat(horse_stats, x, 'horse_win_rate', 0)) # default 0 for new horse
    program_df['horse_races'] = program_df['horse_name'].apply(lambda x: get_stat(horse_stats, x, 'horse_races', 0))
    
    # Parse Gallops
    program_df = parse_gallop_features(program_df)
    
    return program_df

def predict_race(args):
    print(f"Predicting for {args.city} on {args.date} using LightGBM Phase 2 Engine...")
    
    # 1. Load Program
    df = load_program(args.city, args.date)
    if df.empty:
        print("No races found for this date/city.")
        return

    # 2. Enrich with Stats
    df = get_latest_stats(df)

    # 3. Load Model & Encoders
    try:
        # Load Phase 7 Model (HP/Weight Interaction)
        model = joblib.load('tjk_model_v7_complete.pkl')
        le_track = joblib.load('le_track_v7.pkl')
        le_city = joblib.load('le_city_v7.pkl')
    except FileNotFoundError:
        print("v7 model not found! Fallback to v5...")
        try:
            model = joblib.load('tjk_model_v5_critical.pkl')
            le_track = joblib.load('le_track_v5.pkl')
            le_city = joblib.load('le_city_v5.pkl')
        except:
             print("No model found. Pleaase run training.")
             return

    # 4. Prepare Features
    # Handle known categories
    def safe_transform(le, col_data):
        # If label not in encoder, map to something (e.g., mode or 0)
        # For simplicity, use 0 if unknown.
        known_classes = set(le.classes_)
        return col_data.apply(lambda x: le.transform([str(x)])[0] if str(x) in known_classes else 0)

    df['track_encoded'] = safe_transform(le_track, df['track_type'])
    df['city_encoded'] = safe_transform(le_city, df['city'])
    
    # Phase 5.5: Apply same scaling as training
    df['jockey_win_rate_scaled'] = df['jockey_win_rate'] * 0.5
    df['jockey_races_scaled'] = df['jockey_races'] * 0.5
    
    # Prize (from race) - default 0 for now (TODO: scrape prize in program entries)
    df['prize_numeric'] = 0 
    
    # Phase 6 & 7: HP & Weight Features
    if 'hp' not in df.columns: df['hp'] = 0
    # Track Condition (default dry for inference unless passed as arg - TODO)
    df['track_wet'] = 0 
    
    # 1. HP / Weight Efficiency
    df['weight_clamped'] = df['weight'].clip(lower=40)
    df['hp_per_weight'] = df['hp'] / df['weight_clamped']
    
    # 2. Weight Advantage (Deviation from Race Mean)
    # Group by Race ID to get mean weight
    df['race_mean_weight'] = df.groupby('program_race_id')['weight'].transform('mean')
    df['weight_advantage'] = df['race_mean_weight'] - df['weight']
    
    features = [
        'distance', 'weight', 'track_encoded', 'city_encoded',
        'jockey_win_rate_scaled', 'jockey_races_scaled',
        'trainer_win_rate', 'trainer_races',
        'horse_win_rate', 'horse_races',
        'gallop_speed', 'days_since_gallop',
        'prize_numeric', 'hp', 'track_wet',
        'hp_per_weight', 'weight_advantage'
    ]
    
    # 5. Predict
    # LightGBM expects float for most
    X = df[features].astype(float)
    
    # Predict Probability of Class 1 (Win)
    # Predict Probability of Class 1 (Win)
    probs = model.predict_proba(X)[:, 1]
    df['win_prob'] = probs
    
    # PHASE 6/7: Manual Adjustments DISABLED
    # Model v7 now learns HP/Weight natively.
    # We will rely on the trained model.
    # If needed, we can re-enable small bonuses for specific conditions later.
    
    # 6. Group by Race and Rank
    races = df.groupby('program_race_id')
    
    print("\n--- PREDICTIONS (LightGBM v7 - HP/Weight Model) ---")
    from analyst import analyze_race
    
    all_races_data = {}

    def validate_race_health(df_race):
        """
        Firewall Phase 4: Check if race data is healthy enough for prediction.
        """
        total = len(df_race)
        if total == 0: return False, "No horses found."
        
        # Critical checks
        zero_weights = df_race[df_race['weight'] < 20] 
        missing_jockeys = df_race[df_race['jockey'].str.len() < 2]
        
        impairment = 0
        reasons = []
        
        if len(zero_weights) > 0:
            impairment += len(zero_weights)
            reasons.append(f"{len(zero_weights)} horses have 0/invalid Weight")
            
        if len(missing_jockeys) > 0:
            impairment += len(missing_jockeys)
            reasons.append(f"{len(missing_jockeys)} horses have missing Jockey")
            
        # HP check (soft warning)
        zero_hp = df_race[df_race['hp'] == 0] if 'hp' in df_race.columns else []
        if len(zero_hp) > total * 0.9: 
             # If almost everyone has 0 HP, it might be a Maiden race or data error.
             # We won't block, but note it.
             pass

        fail_threshold = 0.25 # >25% bad data = Abort
        if impairment / total > fail_threshold:
            return False, f"DATA FIREWALL: Too much missing data ({impairment}/{total}). Reasons: {', '.join(reasons)}"
            
        return True, "Healthy"
    
    for race_id, group in races:
        # FIREWALL CHECK
        is_healthy, msg = validate_race_health(group)
        if not is_healthy:
            print(f"\nRace ID: {race_id} - [SKIPPED]")
            print(f"⚠️  {msg}")
            # Try to trigger a re-scrape here in Phase 5
            continue

        print(f"\nRace ID: {race_id}")
        sorted_horses = group.sort_values('win_prob', ascending=False)
        
        preds_list = []
        rank = 1
        for _, row in sorted_horses.iterrows():
            # Get additional info for display
            # Assuming 'gallop_info' might be a column in 'row' or will be added later.
            # If not present, .get() will return 'N/A'.
            gallop = row.get('gallop_info', 'N/A')
            print(f"{rank}. {row['horse_name']} - Win Prob: {row['win_prob']:.2f} (J.Rate: {row['jockey_win_rate']:.2f}) [Gallop: {gallop}]")
            preds_list.append({
                'program_no': row['program_no'],
                'horse_name': row['horse_name'],
                'win_prob': row['win_prob'],
                'jockey': row['jockey'],
                'weight': row['weight'],
                'last_6_races': row['last_6_races'],
                'hp': row['hp']
            })
            rank += 1
            if rank > 5: break 
            
        if race_id not in all_races_data: all_races_data[race_id] = []
        all_races_data[race_id] = preds_list
        
        # Call Analyst
        analysis = analyze_race(race_id, preds_list, key=args.key, provider="gemini")
        print(f"\n📝 YZ Yorumu: {analysis}")
        print("-" * 40)
        
        time.sleep(2) # Throttle

    # --- Coupon Generation ---
    from coupon_generator import create_coupon, format_coupon_output
    
    print("\n\n🏆 --- TAHMİNİ KUPONLAR --- 🏆")
    
    coupon1 = create_coupon(all_races_data, start_race=1, coupon_type="1. 6'lı Ganyan")
    if coupon1:
        print(format_coupon_output("1. 6'lı Ganyan", coupon1))
        
    last_race_id = max(all_races_data.keys())
    second_start = last_race_id - 5
    if second_start > 1:
        coupon2 = create_coupon(all_races_data, start_race=second_start, coupon_type="2. 6'lı Ganyan")
        if coupon2:
             print(format_coupon_output(f"2. 6'lı Ganyan ({second_start}-{last_race_id}. Koşular)", coupon2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', required=True, help="Date (DD/MM/YYYY)")
    parser.add_argument('--city', required=True, help="City Name")
    parser.add_argument('--key', required=True, help="Gemini API Key")
    args = parser.parse_args()
    
    predict_race(args)
