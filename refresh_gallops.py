
import sys
import os
import pandas as pd
import sqlite3
from datetime import datetime

sys.path.append(os.getcwd())
from production_engine import fetch_gallops_for_program

DB_NAME = "tjk_races.db"
TARGET_DATE = "19/01/2026"

def refresh_gallops():
    print(f"🔄 Refreshing Gallops for {TARGET_DATE}...")
    
    conn = sqlite3.connect(DB_NAME)
    # Get all horses running today in TR cities (or all)
    # Filter for Adana/Istanbul to save time if needed, but parallel is fast.
    query = """
    SELECT pe.horse_id, pe.horse_name 
    FROM program_entries pe
    JOIN program_races pr ON pe.program_race_id = pr.id
    WHERE pr.date = ?
    """
    df = pd.read_sql_query(query, conn, params=(TARGET_DATE,))
    conn.close()
    
    if df.empty:
        print("❌ No horses found for target date.")
        return

    print(f"🐎 Found {len(df)} horses.")
    
    # Use the robust parallel fetcher from production_engine
    fetch_gallops_for_program(df, TARGET_DATE)
    print("✅ Gallop Scrape Complete.")

if __name__ == "__main__":
    refresh_gallops()
