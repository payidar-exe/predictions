import pandas as pd
import sqlite3
import numpy as np

# DB Connection
DB_NAME = "tjk_races.db"

def fetch_data():
    print(f"Fetching data from local DB {DB_NAME}...")
    conn = sqlite3.connect(DB_NAME)
    query = """
    SELECT 
        r.id as race_id, r.date, r.city, r.track_type, r.distance, r.prize, r.track_condition,
        res.horse_name, res.jockey, res.trainer, res.rank, res.weight, res.hp
    FROM results res
    JOIN races r ON res.race_id = r.id
    ORDER BY r.date ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Convert date
    df['date'] = pd.to_datetime(df['date'], dayfirst=True)
    
    # Parse Prize: "129.000 t" -> 129000
    def parse_prize(p):
        if pd.isna(p): return 0
        try:
            clean = str(p).replace('t', '').replace('.', '').strip()
            return int(clean)
        except:
            return 0
    df['prize_numeric'] = df['prize'].apply(parse_prize)
    
    # HP (Handicap Points) - fill NaN with 0
    df['hp'] = df['hp'].fillna(0).astype(int)
    
    # Track Condition: Encode wet/dry
    def parse_track_cond(tc):
        if pd.isna(tc): return 0
        return 1 if 'sulu' in str(tc).lower() or 'ıslak' in str(tc).lower() else 0
    df['track_wet'] = df['track_condition'].apply(parse_track_cond)
    
    # --- PHASE 7: Advanced Feature Interactions ---
    
    # 1. HP / Weight Efficiency
    # Higher HP is good. Lower Weight is good.
    # Formula: HP / Weight
    # Avoid division by zero (weight < 20 is erroneous usually, clamp to 20)
    df['weight_clamped'] = df['weight'].clip(lower=40) 
    df['hp_per_weight'] = df['hp'] / df['weight_clamped']
    
    # 2. Weight Advantage (Deviation from Race Mean)
    # Group by Race to calculate mean weight
    # We have race_id now.
    if 'race_id' in df.columns:
         df['race_mean_weight'] = df.groupby('race_id')['weight'].transform('mean')
         # Positive advantage = Carrying LESS than average
         df['weight_advantage'] = df['race_mean_weight'] - df['weight']
    else:
         df['weight_advantage'] = 0
         
    return df
    
def add_weight_advantage(df, conn):
    # Separate function to handle group-by operations if needed, 
    # or just do it in fetch_data if we pull race_id.
    # Let's modify fetch_data query to include race_id.
    pass

def calculate_rolling_stats(df):
    print("Calculating rolling statistics (this may take a moment)...")
    
    # Target variable: Is Winner? (Rank 1)
    df['is_winner'] = (df['rank'] == 1).astype(int)
    
    # We need to calculate stats considering ONLY past races.
    # GroupBy + Shift + Rolling/Expanding is complex in pandas for multi-keys.
    # A simpler efficient approach for "Past Stats":
    # Iterate through time or use cumsum().
    
    # 1. GLOBAL JOCKEY STATS (Cumulative)
    # Group by Jockey, Sort by Date
    # Calculate cumulative wins and cumulative races BEFORE this race
    
    # Helper to calculate expanding win rate
    def calc_expanding_win_rate(subset, group_col):
        # Sort by date just in case
        subset = subset.sort_values('date')
        
        # Shift 1 to exclude current race from stats
        # cumsum of wins / cumcount of races
        
        # We need to handle the fact that multiple races happen on same day.
        # But for simplicity, we treat row-by-row expansions (approximation)
        # Or better: strictly shift.
        
        wins = subset['is_winner'].shift().fillna(0).cumsum()
        counts = subset['is_winner'].shift().notna().cumsum().fillna(0) # basically row number
        
        subset[f'{group_col}_win_rate'] = wins / counts.replace(0, 1) # avoid div by zero
        subset[f'{group_col}_races'] = counts
        return subset

    # Apply to Jockey
    print("... Jockey stats")
    df = df.groupby('jockey', group_keys=False).apply(lambda x: calc_expanding_win_rate(x, 'jockey'))
    

    # Apply to Trainer
    print("... Trainer stats")
    df = df.groupby('trainer', group_keys=False).apply(lambda x: calc_expanding_win_rate(x, 'trainer'))
    
    # Apply to Horse (Form)
    print("... Horse stats")
    df = df.groupby('horse_name', group_keys=False).apply(lambda x: calc_expanding_win_rate(x, 'horse'))

    # --- PHASE 5: GALLOP INTEGRATION ---
    print("... integrating Gallop data")
    try:
        # 1. Load Gallops
        gallops_query = "SELECT horse_id, date as gallop_date, distance as g_dist, duration as g_sec FROM gallops"
        df_gal = pd.read_sql_query(gallops_query, sqlite3.connect(DB_NAME))
        df_gal['gallop_date'] = pd.to_datetime(df_gal['gallop_date'], dayfirst=True)
        df_gal = df_gal.sort_values('gallop_date')
        
        # 2. Get Map (Name -> ID)
        map_query = "SELECT DISTINCT horse_name, horse_id FROM program_entries WHERE horse_id > 0"
        df_map = pd.read_sql_query(map_query, sqlite3.connect(DB_NAME))
        # Deduplicate map (just in case)
        df_map = df_map.drop_duplicates(subset=['horse_name'])
        
        # 3. Add ID to main DF
        df = df.merge(df_map, on='horse_name', how='left')
        
        # FIX: Ensure horse_id types match for merge_asof
        # If df has NaNs in horse_id, it becomes float. df_gal is int.
        # We'll fill NaN with -1 and convert to int.
        df['horse_id'] = df['horse_id'].fillna(-1).astype(int)
        df_gal['horse_id'] = df_gal['horse_id'].astype(int)
        
        # 4. Filter Gallops (Sanity Check)
        df_gal = df_gal[df_gal['g_sec'] > 0]
        
        # 5. Merge Asof (Find last gallop before race date)
        # Both must be sorted by date
        df = df.sort_values('date')
        
        # Ensure ID match types
        # Drop rows without ID for gallop calc (or keep them with NaNs)
        
        # We need to perform merge_asof BY horse_id.
        # merge_asof requires 'on' column to be sorted. 'by' column is for grouping.
        if not df_gal.empty and 'horse_id' in df.columns:
             # Merge asof
             df_merged = pd.merge_asof(
                 df, 
                 df_gal, 
                 left_on='date', 
                 right_on='gallop_date', 
                 by='horse_id', 
                 direction='backward'
             )
             df = df_merged
             
             # 6. Feature Engineering
             # Days since gallop
             df['days_since_gallop'] = (df['date'] - df['gallop_date']).dt.days
             
             # Gallop Speed (m/s)
             df['gallop_speed'] = df['g_dist'] / df['g_sec']
             
             # Fill NaNs (No gallop found)
             df['days_since_gallop'] = df['days_since_gallop'].fillna(999) # Long time ago
             df['gallop_speed'] = df['gallop_speed'].fillna(0) # Slow / Unknown
             
        else:
            print("Warning: No gallop data available or ID mapping failed.")
            df['days_since_gallop'] = 999
            df['gallop_speed'] = 0
            
    except Exception as e:
        print(f"Error in Gallop Integration: {e}")
        df['days_since_gallop'] = 999
        df['gallop_speed'] = 0

    return df

def save_features(df):
    print("Saving engineered features to 'features_dataset.csv'...")
    df.to_csv('features_dataset.csv', index=False)
    print("Done!")

if __name__ == "__main__":
    raw_df = fetch_data()
    if raw_df.empty:
        print("No data found! Please scrape some historical data first.")
    else:
        processed_df = calculate_rolling_stats(raw_df)
        save_features(processed_df)
        print(processed_df[['date', 'jockey', 'jockey_win_rate', 'is_winner']].tail(10))
