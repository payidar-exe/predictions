#!/usr/bin/env python3
"""
daily_results.py - Akşam 22:00'da çalışır
TJK'dan bugünün sonuçlarını çeker, kupon ayaklarını günceller.
"""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def scrape_today_results():
    """TJK'dan bugünün sonuçlarını çeker"""
    from tjk_scraper.scrape import scrape_range
    
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"📊 Scraping results for {today}...")
    
    scrape_range(today, today)
    print("✅ Results scraped successfully")

def get_race_winners():
    """SQLite'dan kazananları çeker"""
    import sqlite3
    
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "tjk_scraper", "tjk_data.db"
    )
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get all races and their winners (position = 1)
    cursor.execute("""
        SELECT r.city, r.race_no, r.race_time, res.horse_name, res.position
        FROM races r
        JOIN results res ON r.id = res.race_id
        WHERE r.date = ? AND res.position = 1
        ORDER BY r.city, r.race_no
    """, (today,))
    
    winners = {}
    for row in cursor.fetchall():
        city, race_no, race_time, horse_name, position = row
        key = f"{city}_{race_no}"
        winners[key] = {
            "city": city,
            "race_no": race_no,
            "race_time": race_time,
            "winner": horse_name
        }
    
    conn.close()
    return winners

def update_coupon_results():
    """Kuponları sonuçlarla günceller"""
    supabase = get_supabase()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get today's coupons
    response = supabase.table('coupons').select('*').eq('date', today).execute()
    coupons = response.data
    
    if not coupons:
        print("⚠️ No coupons found for today")
        return
    
    # Get winners
    winners = get_race_winners()
    
    for coupon in coupons:
        legs = coupon.get('legs', [])
        total_legs = len(legs)
        won_legs = 0
        
        updated_legs = []
        for leg in legs:
            leg_no = leg.get('leg_no', 0)
            horses = leg.get('horses', [])
            horse_names = [h['horse_name'] for h in horses]
            
            # Find matching race winner
            key = f"{coupon['city']}_{leg_no}"
            winner_info = winners.get(key, {})
            actual_winner = winner_info.get('winner', '')
            
            # Check if any of our picks won
            leg_won = actual_winner in horse_names
            
            if leg_won:
                won_legs += 1
                leg['leg_result'] = 'won'
            else:
                leg['leg_result'] = 'lost'
            
            leg['actual_winner'] = actual_winner
            updated_legs.append(leg)
        
        # Determine overall coupon status
        coupon_won = won_legs == total_legs
        
        # Calculate winning amount (mock calculation)
        winning_amount = 0
        if coupon_won:
            # Parse subtitle for bet amount and apply multiplier
            winning_amount = 5000 + (won_legs * 1000)  # Simplified
        
        # Update coupon
        update_data = {
            'legs': updated_legs,
            'status': 'won' if coupon_won else 'lost',
            'winning_amount': winning_amount
        }
        
        supabase.table('coupons').update(update_data).eq('id', coupon['id']).execute()
        
        status_emoji = "🎉" if coupon_won else "❌"
        print(f"{status_emoji} {coupon['city']}: {won_legs}/{total_legs} legs won")
    
    print("\n✅ Results updated!")

def main():
    print("=" * 50)
    print(f"📊 Daily Results - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    
    # Step 1: Scrape results
    try:
        scrape_today_results()
    except Exception as e:
        print(f"❌ Scrape failed: {e}")
        return 1
    
    # Step 2: Update coupons
    try:
        update_coupon_results()
    except Exception as e:
        print(f"❌ Update failed: {e}")
        return 1
    
    print("\n✅ Daily results complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
