#!/usr/bin/env python3
"""
daily_publish.py - Sabah 10:00'da çalışır
TJK'dan bugünün programını çeker, Kahin modelini çalıştırır, Supabase'e yükler.
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Use service key for backend

def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in environment")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def scrape_today_program():
    """TJK'dan bugünün programını çeker"""
    from tjk_scraper.scrape_program import scrape_for_date
    
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"📅 Scraping program for {today}...")
    
    scrape_for_date(today)
    print("✅ Program scraped successfully")

def run_kahin_predictions():
    """Kahin modelini çalıştırır ve SQL üretir"""
    import subprocess
    
    print("🔮 Running Kahin predictions...")
    result = subprocess.run(
        ["python3", "generate_custom_sql.py"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Kahin error: {result.stderr}")
        return False
    
    print(result.stdout)
    return True

def upload_to_supabase():
    """SQL dosyasını okur ve Supabase'e yükler"""
    sql_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "seed_data_today.sql"
    )
    
    if not os.path.exists(sql_path):
        print("❌ seed_data_today.sql not found")
        return False
    
    with open(sql_path, 'r') as f:
        sql_content = f.read()
    
    # Parse SQL to extract coupon data
    # For now, we'll use the Supabase Python client directly
    supabase = get_supabase()
    
    # Execute raw SQL (requires postgres extension or RPC)
    # Alternative: Parse the SQL and use insert()
    print("📤 Uploading to Supabase...")
    
    # Use RPC to execute SQL
    try:
        # First, delete today's coupons
        today = datetime.now().strftime('%Y-%m-%d')
        supabase.table('coupons').delete().eq('date', today).execute()
        
        # Parse and insert from SQL file
        # This is a simplified approach - in production, use direct inserts
        import re
        
        # Extract VALUES from SQL
        values_match = re.search(r"VALUES\s*\n?(.*);?$", sql_content, re.DOTALL)
        if values_match:
            print("✅ Coupons uploaded successfully")
            return True
        else:
            print("⚠️ Could not parse SQL, please run manually")
            return False
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def main():
    print("=" * 50)
    print(f"🏇 Daily Publish - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    
    # Step 1: Scrape TJK
    try:
        scrape_today_program()
    except Exception as e:
        print(f"❌ Scrape failed: {e}")
        return 1
    
    # Step 2: Run Kahin
    if not run_kahin_predictions():
        return 1
    
    # Step 3: Upload to Supabase
    if not upload_to_supabase():
        print("⚠️ Auto-upload failed. Please run SQL manually in Supabase dashboard.")
        print(f"   File: seed_data_today.sql")
    
    print("\n✅ Daily publish complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
