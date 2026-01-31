#!/usr/bin/env python3
"""
Bulk Galop Scraper - 20 Concurrent Workers
Collects galop data for all horses in database for model retraining
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

DB_NAME = "tjk_races.db"

def fetch_single_horse_gallops(horse_id, horse_name):
    """Fetch galop data for a single horse from TJK."""
    url = f"https://www.tjk.org/TR/YarisSever/Query/Page/IdmanIstatistikleri?QueryParameter_AtId={horse_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    gallops = []
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            # The galop table is the one that contains '1200m' or 'Tarihi' headers
            tables = soup.find_all('table')
            target_table = None
            for t in tables:
                if '1200m' in t.get_text() or 'Tarihi' in t.get_text():
                    target_table = t
                    break
            
            if not target_table: 
                # Fallback to first table if only one exists (and headers weird)
                if len(tables) > 0: target_table = tables[0]
                else: return []
            
            rows = target_table.find_all('tr')
            for r in rows:
                if not r.find('td'): continue
                cols = [td.get_text().strip() for td in r.find_all('td')]
                
                # Check column count (needs at least 13 for date)
                if len(cols) >= 13:
                    # New Layout Indices:
                    # 0: Name, 4-10: Dists, 11: Status, 12: Date, 13: City, 15: Track
                    
                    g_date = cols[12] # Date
                    
                    # Determine Distance & Time
                    # Dist cols indices: 4(1400), 5(1200), 6(1000), 7(800), 8(600), 9(400), 10(200)
                    dist_map = {4:1400, 5:1200, 6:1000, 7:800, 8:600, 9:400, 10:200}
                    
                    g_dist = 0
                    g_time_str = ""
                    g_time = 0.0
                    
                    # Iterate to find the longest distance recorded
                    for idx in [4, 5, 6, 7, 8, 9, 10]:
                        if idx < len(cols) and cols[idx].strip():
                            # Found a time
                            d = dist_map.get(idx, 0)
                            t_s = cols[idx].strip()
                            # Perform parsing
                            try:
                                # 0.51.50 -> 51.5s
                                parts = t_s.split('.')
                                val = 0.0
                                if len(parts) == 3: # min.sec.ms
                                    val = float(parts[0])*60 + float(parts[1]) + float(parts[2])/100.0
                                elif len(parts) == 2: # sec.ms (rare but possible)
                                    val = float(parts[0]) + float(parts[1])/100.0
                                elif len(parts) == 1: # sec?
                                    val = float(parts[0])
                                
                                if val > 0:
                                    # Use this if it's longer distance or first one found
                                    # Logic: Usually we want the Main Work.
                                    # TJK puts main work in respective column.
                                    # If multiple (e.g. 800 and 400), typically 800 is the main one.
                                    # So we take the largest distance found.
                                    if d > g_dist:
                                        g_dist = d
                                        g_time = val
                                        g_time_str = t_s
                            except: pass
                    
                    if g_dist > 0:
                        # Rank is missing in new layout
                        g_rank = 0
                        
                        gallops.append({
                            'horse_id': horse_id,
                            'horse_name': horse_name,
                            'date': g_date,
                            'distance': g_dist,
                            'time_sec': g_time,
                            'rank': g_rank
                        })
    except Exception as e:
        pass
    
    return gallops

def main():
    conn = sqlite3.connect(DB_NAME)
    
    # Get ALL horses from program_entries that we don't already have galops for
    print("🔍 Finding horses needing galop data...")
    
    # Get horses with valid IDs from program_entries
    all_horses = conn.execute("""
        SELECT DISTINCT pe.horse_id, pe.horse_name 
        FROM program_entries pe 
        WHERE pe.horse_id > 0
    """).fetchall()
    
    # Get horses we already have galops for
    existing = set(r[0] for r in conn.execute("SELECT DISTINCT horse_id FROM gallops").fetchall())
    
    # Filter to only horses without galops
    horses_to_fetch = [(h_id, h_name) for h_id, h_name in all_horses if h_id not in existing]
    
    print(f"📊 Stats: {len(all_horses)} total horses, {len(existing)} already have galops")
    print(f"🏇 Fetching galops for {len(horses_to_fetch)} new horses with 20 workers...")
    print("=" * 60)
    
    start_time = time.time()
    total_gallops = 0
    completed = 0
    
    # Parallel fetch with 20 workers
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(fetch_single_horse_gallops, h_id, h_name): (h_id, h_name) 
            for h_id, h_name in horses_to_fetch
        }
        
        batch_gallops = []
        
        for future in as_completed(futures):
            completed += 1
            try:
                gallops = future.result()
                if gallops:
                    batch_gallops.extend(gallops)
                    total_gallops += len(gallops)
            except: pass
            
            # Progress every 50 horses
            if completed % 50 == 0:
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (len(horses_to_fetch) - completed) / rate if rate > 0 else 0
                print(f"  ⏳ {completed}/{len(horses_to_fetch)} at | {total_gallops} galop | {rate:.1f} at/s | ETA: {eta/60:.1f}dk")
                
                # Save batch to DB
                if batch_gallops:
                    c = conn.cursor()
                    for g in batch_gallops:
                        try:
                            c.execute('''
                                INSERT OR IGNORE INTO gallops (horse_id, horse_name, date, city, track_type, distance, time_sec, rank, description)
                                VALUES (?, ?, ?, '', '', ?, ?, ?, '')
                            ''', (g['horse_id'], g['horse_name'], g['date'], g['distance'], g['time_sec'], g['rank']))
                        except: pass
                    conn.commit()
                    batch_gallops = []
        
        # Save remaining
        if batch_gallops:
            c = conn.cursor()
            for g in batch_gallops:
                try:
                    c.execute('''
                        INSERT OR IGNORE INTO gallops (horse_id, horse_name, date, city, track_type, distance, time_sec, rank, description)
                        VALUES (?, ?, ?, '', '', ?, ?, ?, '')
                    ''', (g['horse_id'], g['horse_name'], g['date'], g['distance'], g['time_sec'], g['rank']))
                except: pass
            conn.commit()
    
    elapsed = time.time() - start_time
    
    # Final stats
    final_count = conn.execute("SELECT COUNT(*) FROM gallops").fetchone()[0]
    conn.close()
    
    print("=" * 60)
    print(f"✅ TAMAMLANDI!")
    print(f"   Süre: {elapsed/60:.1f} dakika")
    print(f"   İşlenen at: {completed}")
    print(f"   Yeni galop: {total_gallops}")
    print(f"   Toplam galop (DB): {final_count}")

if __name__ == "__main__":
    main()
