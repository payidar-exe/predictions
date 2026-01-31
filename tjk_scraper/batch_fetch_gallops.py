
import sqlite3
import requests
from bs4 import BeautifulSoup
import time
import random
import re

DB_NAME = "tjk_races.db"

def fetch_gallop_history(horse_id):
    if not horse_id: return []
    
    url = f"https://www.tjk.org/TR/YarisSever/Query/Page/IdmanIstatistikleri?QueryParameter_AtId={horse_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    gallops = []
    # Retry loop
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                table = soup.find('table')
                if table:
                    rows = table.find_all('tr')
                    # Row 0 is header. Data starts row 1.
                    for i in range(1, len(rows)):
                        row = rows[i]
                        cols = row.find_all('td')
                        if len(cols) > 13:
                            # Map based on debug output Step 1260
                            # [4]1400, [5]1200, [6]1000, [7]800, [8]600, [9]400, [10]200
                            # [12]Date, [13]City, [15]Track
                            
                            date_str = cols[12].get_text(strip=True)
                            city = cols[13].get_text(strip=True)
                            track = cols[15].get_text(strip=True)
                            
                            # Find largest distance
                            dist = 0
                            time_txt = ""
                            
                            # Check longest to shortest
                            dist_map = {4:1400, 5:1200, 6:1000, 7:800, 8:600, 9:400, 10:200}
                            for col_idx in sorted(dist_map.keys()): # 4..10
                                val = cols[col_idx].get_text(strip=True)
                                if val and len(val) > 3: # simple check for "0.00.00"
                                    dist = dist_map[col_idx]
                                    time_txt = val
                                    break # Take the longest one
                                    
                            if dist == 0: continue # Empty row
                            
                            # Parse Duration
                            duration = 0.0
                            try:
                                parts = time_txt.replace(':', '.').split('.')
                                if len(parts) == 3: # m.ss.ms (0.58.40)
                                    # parts[2] is likely cs (centiseconds) 
                                    duration = float(parts[0])*60 + float(parts[1]) + float(parts[2])/100
                                elif len(parts) == 2: # ss.ms
                                    duration = float(parts[0]) + float(parts[1])/100
                                else:
                                    duration = float(time_txt)
                            except: pass
                            
                            if duration > 0:
                                gallops.append({
                                    'horse_id': horse_id,
                                    'date': date_str,
                                    'city': city,
                                    'distance': dist,
                                    'duration': duration,
                                    'track_type': track,
                                    'raw_time': time_txt
                                })
                break # Success
            else:
                 time.sleep(1) # Retry
        except Exception:
            time.sleep(1)
            
    return gallops

def process_queue():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Get Distinct Active Horses first (Priority: CURRENT BURSA RACE)
    # Filter for Bursa 12/01 horses that haven't been scraped yet
    c.execute("""
        SELECT DISTINCT pe.horse_id, pe.horse_name 
        FROM program_entries pe
        JOIN program_races pr ON pe.program_race_id = pr.id
        WHERE pr.city LIKE '%Bursa%' AND pr.date = '12/01/2026'
          AND (pe.gallop_info = 'QUEUE' OR pe.gallop_info IS NULL)
    """)
    active_horses = c.fetchall()
    
    print(f"Found {len(active_horses)} active horses to fetch gallops for.")
    
    # Check which ones we already fetched recently? 
    # For now, just simplistic fetch.
    
    count = 0
    for h_id, h_name in active_horses:
        count += 1
        print(f"[{count}/{len(active_horses)}] Fetching History for {h_name} ({h_id})...")
        
        gallops = fetch_gallop_history(h_id)
        
        if gallops:
            latest = gallops[0]
            latest_str = f"{latest['date']} - {latest['distance']}m: {latest['raw_time']}"
            
            # Update program_entries (Legacy)
            c.execute("UPDATE program_entries SET gallop_info = ? WHERE horse_id = ?", (latest_str, h_id))
            
            # Insert into gallops table (History)
            inserted = 0
            for g in gallops:
                try:
                    c.execute('''
                        INSERT OR IGNORE INTO gallops (horse_id, date, city, distance, duration, track_type)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (g['horse_id'], g['date'], g['city'], g['distance'], g['duration'], g['track_type']))
                    if c.rowcount > 0: inserted += 1
                except:
                    pass
            print(f"  -> Saved {inserted} new gallops.")
        else:
            print("  -> No gallops found.")
            
        conn.commit()
        time.sleep(0.3) # Fast but polite
        
    conn.close()
    print("Batch processing complete.")

if __name__ == "__main__":
    process_queue()
