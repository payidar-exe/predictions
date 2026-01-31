
import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import random
import re

DB_NAME = "tjk_races.db"

def clean_text(text):
    if text:
        return text.strip().replace('\n', '').replace('\r', '').replace('  ', '')
    return None

def fetch_gallops_for_horse(horse_id, existing_dates=None):
    url = f"https://www.tjk.org/TR/YarisSever/Query/Page/IdmanIstatistikleri?QueryParameter_AtId={horse_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    gallops = []
    
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                table = soup.find('table')
                if not table: return []
                
                rows = table.find_all('tr')
                for r in rows:
                    if not r.find('td'): continue # Skip header
                    
                    cols = [clean_text(td.get_text()) for td in r.find_all('td')]
                    # Typical Columns: Tarih | Sehir | Pist | Mesafe | Derece | Galop Sırası | ...
                    if len(cols) >= 6:
                        g_date = cols[0]
                        g_city = cols[1]
                        g_track = cols[2]
                        g_dist = 0
                        try:
                            g_dist = int(cols[3])
                        except: pass
                        
                        g_time = 0.0
                        try:
                            # 0.50.2 or 1.02.10
                            parts = cols[4].split('.')
                            if len(parts) == 3: # min.sec.ms
                                g_time = float(parts[0])*60 + float(parts[1]) + float(parts[2])/100.0
                            elif len(parts) == 2: # sec.ms
                                g_time = float(parts[0]) + float(parts[1])/100.0
                        except: pass
                        
                        g_rank = 0
                        try:
                            # 1 / 45 -> Extract 1
                            rank_part = cols[5].split('/')[0].strip()
                            g_rank = int(rank_part)
                        except: pass
                        
                        if existing_dates and g_date in existing_dates:
                            continue # Skip existing
                            
                        gallops.append({
                            'date': g_date,
                            'city': g_city,
                            'track': g_track,
                            'dist': g_dist,
                            'time': g_time,
                            'rank': g_rank,
                            'desc': cols[4] # Keeping original time string
                        })
                break # Success
            else:
                 time.sleep(2) # Retry on non-200
        except Exception as e:
            # print(f"Error for horse {horse_id}: {e}") # Silent retry
            time.sleep(2 ** (attempt + 1))
            
    return gallops

def main():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Get Horses to Scrape
    print("🔍 Identifying horses needing gallop data...")
    c.execute("SELECT DISTINCT horse_id, horse_name FROM program_entries WHERE horse_id > 0")
    horses = c.fetchall()
    
    print(f"Found {len(horses)} UNIQUE horses.")
    
    count = 0
    total = len(horses)
    
    for h_id, h_name in horses:
        count += 1
        
        # Check existing
        c.execute("SELECT date FROM gallops WHERE horse_id=?", (h_id,))
        existing_dates = {row[0] for row in c.fetchall()}
        
        if len(existing_dates) > 50: # Assume up to date if has history
            # Actually, we should check recency, but for now let's just skip "full" ones to save time
            # SKIP optimization for now to ensure we get LATEST
            pass

        print(f"[{count}/{total}] Scraping gallops for {h_name} ({h_id})...")
        
        new_gallops = fetch_gallops_for_horse(h_id, existing_dates)
        
        if new_gallops:
            print(f"   ✅ Found {len(new_gallops)} new records.")
            for g in new_gallops:
                try:
                    c.execute('''
                        INSERT OR IGNORE INTO gallops (horse_id, horse_name, date, city, track_type, distance, time_sec, rank, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (h_id, h_name, g['date'], g['city'], g['track'], g['dist'], g['time'], g['rank'], g['desc']))
                except Exception as e:
                    print(f"Database Error: {e}")
            conn.commit()
        else:
            print("   ⚠️ No new data.")
            
        time.sleep(random.uniform(0.1, 0.3)) # Be gentle
        
    conn.close()
    print("🎉 Gallop Scraping Complete.")

if __name__ == "__main__":
    main()
