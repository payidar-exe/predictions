#!/usr/bin/env python3
"""
Supabase Sync - Push Forecasts to Production Database
======================================================
Reads generated forecasts from local SQLite/SQL files and pushes
them to the Supabase production database.

Uses Supabase REST API with service role key or anon key.
"""

import json
import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path
import requests

# Supabase Configuration
SUPABASE_URL = "https://nmdiepowxhctapvkfomm.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5tZGllcG93eGhjdGFwdmtmb21tIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgwODA3MTIsImV4cCI6MjA4MzY1NjcxMn0.xm6w9pqsde2NqqGsCO5Y5k8EnqK4FaJlOWGwiw4Xrl0"

# For write operations, ideally use service_role key (set as env var)
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", SUPABASE_ANON_KEY)

# Local paths
PROJECT_DIR = Path(__file__).parent.absolute()
DB_PATH = PROJECT_DIR / "tjk_races.db"
FORECASTS_SQL = PROJECT_DIR / "daily_forecasts.sql"


def supabase_request(method: str, endpoint: str, data: dict = None) -> dict:
    """Make authenticated request to Supabase REST API."""
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    response = requests.request(method, url, headers=headers, json=data)
    
    if response.status_code >= 400:
        print(f"❌ API Error: {response.status_code}")
        print(f"   Response: {response.text[:500]}")
        return None
    
    try:
        return response.json()
    except:
        return {"status": "ok"}


def get_today_forecasts() -> list:
    """Read forecasts from local database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    today = datetime.now().strftime("%d/%m/%Y")
    
    # Check if daily_forecasts table exists
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='daily_forecasts'
    """)
    
    if not cursor.fetchone():
        print("⚠️ No daily_forecasts table found. Creating from program data...")
        return generate_forecasts_from_program(conn, today)
    
    # Get forecasts for today
    query = """
        SELECT df.*, pr.city, pr.race_no, pr.date
        FROM daily_forecasts df
        JOIN program_races pr ON df.program_race_id = pr.id
        WHERE pr.date = ?
        ORDER BY pr.city, pr.race_no, df.score DESC
    """
    
    rows = conn.execute(query, (today,)).fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def generate_forecasts_from_program(conn, date: str) -> list:
    """Fallback: Generate simplified forecasts from program_entries."""
    query = """
        SELECT pe.*, pr.city, pr.race_no, pr.date, pr.track_type
        FROM program_entries pe
        JOIN program_races pr ON pe.program_race_id = pr.id
        WHERE pr.date = ?
        ORDER BY pr.city, pr.race_no
    """
    
    rows = conn.execute(query, (date,)).fetchall()
    return [dict(row) for row in rows]


def build_coupon_payload(city: str, date: str, forecasts: list) -> dict:
    """Build coupon JSON payload for Supabase insertion."""
    # Group by race_no to form legs
    races = {}
    for f in forecasts:
        rno = f['race_no']
        if rno not in races:
            races[rno] = []
        races[rno].append(f)
    
    # Sort race numbers and take last 6 (standard altılı)
    race_nos = sorted(races.keys())[-6:]
    
    legs = []
    for i, rno in enumerate(race_nos):
        entries = sorted(races[rno], key=lambda x: -x.get('score', 0))
        
        # Take top 2-5 per leg (smart selection based on scores)
        top_score = entries[0].get('score', 0) if entries else 0
        selection_count = 2 if top_score > 0.6 else 3 if top_score > 0.4 else 4
        selected = entries[:min(selection_count, len(entries))]
        
        horses = []
        for j, h in enumerate(selected):
            horses.append({
                "program_no": h.get('program_no', j+1),
                "horse_name": h.get('horse_name', 'Unknown'),
                "jockey_name": h.get('jockey'),
                "ai_score": int(h.get('score', 0.5) * 100),
                "is_banko": j == 0 and top_score > 0.6,
                "ai_note": h.get('ai_comment', None)
            })
        
        legs.append({
            "leg_no": rno,
            "race_time": h.get('race_time', '--:--'),
            "field_size": len(entries),
            "horses": horses
        })
    
    # Format date for Supabase (YYYY-MM-DD)
    try:
        dt = datetime.strptime(date, "%d/%m/%Y")
        formatted_date = dt.strftime("%Y-%m-%d")
    except:
        formatted_date = datetime.now().strftime("%Y-%m-%d")
    
    return {
        "date": formatted_date,
        "city": city.split("  ")[0],  # Remove "(X. Y.G.)" suffix
        "type": "premium",
        "star_cost": 5,
        "title": f"{city.split('  ')[0]} Altılı Ganyan",
        "subtitle": "Kahin AI × Kuantum Analiz",
        "status": "pending",
        "legs": legs
    }


def sync_to_supabase(forecasts: list):
    """Push forecasts to Supabase as coupons."""
    if not forecasts:
        print("⚠️ No forecasts to sync.")
        return False
    
    # Group by city
    cities = {}
    for f in forecasts:
        city = f['city']
        if city not in cities:
            cities[city] = []
        cities[city].append(f)
    
    print(f"📤 Syncing {len(cities)} cities to Supabase...")
    
    success_count = 0
    for city, city_forecasts in cities.items():
        date = city_forecasts[0].get('date', datetime.now().strftime("%d/%m/%Y"))
        
        # Build payload
        coupon = build_coupon_payload(city, date, city_forecasts)
        
        # Check if coupon already exists for this date/city
        formatted_date = coupon['date']
        city_name = coupon['city']
        
        # Try to find existing
        existing = supabase_request(
            "GET", 
            f"coupons?date=eq.{formatted_date}&city=eq.{city_name}&select=id"
        )
        
        if existing and len(existing) > 0:
            # Update existing
            coupon_id = existing[0]['id']
            result = supabase_request("PATCH", f"coupons?id=eq.{coupon_id}", coupon)
            action = "Updated"
        else:
            # Insert new
            result = supabase_request("POST", "coupons", coupon)
            action = "Created"
        
        if result:
            print(f"   ✅ {action}: {city_name} ({formatted_date})")
            success_count += 1
        else:
            print(f"   ❌ Failed: {city_name}")
    
    print(f"\n📊 Sync complete: {success_count}/{len(cities)} cities")
    return success_count == len(cities)


def main():
    """Main sync flow."""
    print("🔄 Supabase Sync Starting...")
    print(f"   Project: {PROJECT_DIR}")
    print(f"   Database: {DB_PATH}")
    
    # Get forecasts
    forecasts = get_today_forecasts()
    print(f"   Found {len(forecasts)} forecast entries")
    
    if len(forecasts) == 0:
        print("⚠️ No forecasts found for today. Nothing to sync.")
        return 1
    
    # Sync to Supabase
    success = sync_to_supabase(forecasts)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
