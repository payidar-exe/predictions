import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import argparse
from datetime import datetime, timedelta

DB_NAME = "tjk_races.db"

def init_program_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Create tables for upcoming programs
    c.execute('''
        CREATE TABLE IF NOT EXISTS program_races (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            city TEXT,
            race_no INTEGER,
            time TEXT,
            race_type TEXT,
            distance TEXT,
            track_type TEXT,
            prize TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS program_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_race_id INTEGER,
            program_no INTEGER,
            horse_name TEXT,
            age TEXT,
            sire TEXT,
            dam TEXT,
            weight REAL,
            jockey TEXT,
            owner TEXT,
            trainer TEXT,
            start_box INTEGER,
            hp INTEGER,
            last_6_races TEXT,
            kgs INTEGER,
            s20 INTEGER,
            best_rating TEXT,
            agf TEXT,
            horse_id INTEGER,
            jockey_id INTEGER,
            gallop_info TEXT,
            FOREIGN KEY(program_race_id) REFERENCES program_races(id)
        )
    ''')
    conn.commit()
    conn.close()

def clean_text(text):
    if text:
        return text.strip().replace('\n', '').replace('\r', '').replace('  ', '')
    return None

def get_program_page(date_str):
    url = f"https://www.tjk.org/TR/YarisSever/Info/Page/GunlukYarisProgrami?QueryParameter_Tarih={date_str}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except Exception as e:
        print(f"Error fetching program: {e}")
        return None

def parse_program_city_links(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    city_links = []
    tabs = soup.find('ul', class_='gunluk-tabs')
    if tabs:
        for a in tabs.find_all('a'):
            href = a.get('href')
            city_name = a.get_text(strip=True)
            if href:
                # The href usually is like /TR/YarisSever/Info/Sehir/GunlukYarisProgrami?SehirId=...
                city_links.append({'name': city_name, 'url': "https://www.tjk.org" + href})
    return city_links

def parse_program_details(html_content, date_str, city_name):
    soup = BeautifulSoup(html_content, 'html.parser')
    race_containers = soup.select('div.races-panes > div[sehir]')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    print(f"Stats: Found {len(race_containers)} races in {city_name}.")
    
    for race_div in race_containers:
        # ... (Same Race Info Parsing) ...
        race_no_tag = race_div.select_one('h3.race-no a')
        race_no = 0
        race_time = ""
        if race_no_tag:
            txt = race_no_tag.get_text(strip=True)
            if "Koşu" in txt:
                parts = txt.split('Koşu')
                try:
                    race_no = int(parts[0].replace('.', ''))
                    race_time = parts[1].strip()
                except: pass
        
        config_tag = race_div.select_one('h3.race-config')
        race_type = ""
        distance = ""
        track_type = ""
        if config_tag:
            config_full = config_tag.get_text(" ", strip=True)
            parts = config_full.split(',')
            if len(parts) > 0: race_type = parts[0].strip()
            dist_match = re.search(r'(\d{4})\s+(Kum|Çim|Sentetik)', config_full, re.IGNORECASE)
            if dist_match:
                distance = dist_match.group(1)
                track_type = dist_match.group(2)
        
        prize = "0"
        prize_dl = race_div.find('dl')
        if prize_dl:
            dd = prize_dl.find('dd')
            if dd: prize = clean_text(dd.get_text())
            
        c.execute('''
            INSERT INTO program_races (date, city, race_no, time, race_type, distance, track_type, prize)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date_str, city_name, race_no, race_time, race_type, distance, track_type, prize))
        race_id = c.lastrowid
        
        # 2. Entries (Horses)
        table = race_div.select_one('table.tablesorter tbody')
        if not table: continue
            
        rows = table.find_all('tr')
        for row in rows:
            try:
                # ... (Basic                # Horse No
                prog_no = 0
                try:
                    # Try first column (usually the No column)
                    first_td = row.find('td')
                    if first_td:
                        txt = clean_text(first_td.get_text())
                        if txt.isdigit(): prog_no = int(txt)
                except:
                    prog_no = 0
                
                # Horse ID & Name
                horse_id = 0
                horse_name = "Unknown"
                horse_tag = row.select_one('.gunluk-GunlukYarisProgrami-AtAdi a') or row.select_one('.gunluk-GunlukYarisProgrami-AtAdi3 a')
                if horse_tag:
                    horse_name = clean_text(horse_tag.get_text()).split('(')[0].strip()
                    href = horse_tag.get('href', '')
                    # Extract ID: ...QueryParameter_AtId=106845...
                    match = re.search(r'QueryParameter_AtId=(\d+)', href)
                    if match: horse_id = int(match.group(1))

                # Jokey ID & Name (Fixed CSS Class Name: JokeAdi)
                jockey_id = 0
                jockey = ""
                # Note: The class name on TJK is 'JokeAdi' (missing y)
                jockey_tag = row.select_one('.gunluk-GunlukYarisProgrami-JokeAdi a') 
                jocke_cell = row.select_one('.gunluk-GunlukYarisProgrami-JokeAdi')
                
                if jockey_tag:
                    jockey = clean_text(jockey_tag.get_text())
                    href = jockey_tag.get('href', '')
                    match = re.search(r'QueryParameter_JokeyId=(\d+)', href)
                    if match: jockey_id = int(match.group(1))
                elif jocke_cell:
                    jockey = clean_text(jocke_cell.get_text()) # No link case (Apprentice?)
                
                # Weight: Handle "50+2.00Fazla Kilo" or "58.5" or "58"
                weight_tag = row.select_one('.gunluk-GunlukYarisProgrami-Kilo')
                weight_txt = clean_text(weight_tag.get_text()) if weight_tag else "0"
                
                weight = 0.0
                try:
                    # Clean up: "58" -> 58.0
                    # "50+2.00" -> 52.0
                    w_clean = weight_txt.replace(',', '.')
                    
                    if '+' in w_clean:
                        parts = w_clean.split('+')
                        base = float(re.search(r"(\d+\.?\d*)", parts[0]).group(1))
                        extra = float(re.search(r"(\d+\.?\d*)", parts[1]).group(1)) if len(parts) > 1 else 0
                        weight = base + extra
                    else:
                        match = re.search(r"(\d+\.?\d*)", w_clean)
                        if match: weight = float(match.group(1))
                except Exception as e:
                    # Fallback
                    weight = 0.0

                # HP (Handicap Point)
                hp = 0
                hp_tag = row.select_one('.gunluk-GunlukYarisProgrami-HandikapPuani')
                hp_txt = ""
                
                if hp_tag:
                    hp_txt = clean_text(hp_tag.get_text())
                    if 'Adana' in city_name: print(f"   [DEBUG] Found HP Tag: '{hp_txt}'")
                else:
                    # Fallback: Try column index 10 (0-based) -> 11th column
                    # Standard TJK Program Columns:
                    # 0:No, 1:AtIsmi, 2:Yas, 3:Orijin(B-K), 4:Kilo, 5:Jokey, 6:Sahip, 7:Antrenor, 8:St, 9:HP, 10:Son 6
                    # Wait, let's verify.
                    # Usually: No, At, Yas, Orijin, Kilo, Jokey, Sahip, Antrenor, Start, HP, Son 6 Y, KGS, s20...
                    tds = row.find_all('td')
                    if len(tds) > 10:
                        candidates = [9, 10]
                        for idx in candidates:
                            txt = clean_text(tds[idx].get_text())
                            if txt.isdigit() and len(txt) <= 3:
                                hp_txt = txt
                                if 'Adana' in city_name: print(f"   [DEBUG] Fallback Col {idx}: '{hp_txt}'")
                                break
                    if 'Adana' in city_name and not hp_txt:
                        print(f"   [DEBUG] NO HP. Row cols: {[clean_text(t.get_text()) for t in tds]}")
                    if len(tds) > 10:
                        # Try index 9 or 10
                        # Let's search for a 2-3 digit number in likely columns
                        candidates = [9, 10]
                        for idx in candidates:
                            txt = clean_text(tds[idx].get_text())
                            # HP is usually an integer like "38" or "102"
                            # Not "30 gün", not "2024"
                            if txt.isdigit() and len(txt) <= 3:
                                hp_txt = txt
                                break

                if hp_txt:
                    try:
                        # "38", "55", etc.
                        hp_match = re.search(r'(\d+)', hp_txt)
                        if hp_match: hp = int(hp_match.group(1))
                    except: hp = 0
                
                # Owner (Sahip) & Trainer (Antrenor)
                owner = ""
                trainer = ""
                tds = row.find_all('td')
                if len(tds) > 8:
                    owner_tag = tds[6]
                    trainer_tag = tds[7]
                    owner = clean_text(owner_tag.get_text())
                    trainer = clean_text(trainer_tag.get_text())

                # Fetch Phase 3 Stats (Gallops)
                gallop_info = "QUEUE"
                
                # Insert
                c.execute('''
                    INSERT INTO program_entries (
                        program_race_id, program_no, horse_name, weight, jockey, 
                        horse_id, jockey_id, gallop_info, hp, owner, trainer
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (race_id, prog_no, horse_name, weight, jockey, horse_id, jockey_id, gallop_info, hp, owner, trainer))
                
            except Exception as e:
                print(f"Error parsing row: {e}")

    conn.commit()
    conn.close()

def fetch_gallop_stats(horse_id):
    # Fetch dedicated page: /Page/IdmanIstatistikleri?QueryParameter_AtId=...
    url = f"https://www.tjk.org/TR/YarisSever/Query/Page/IdmanIstatistikleri?QueryParameter_AtId={horse_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    try:
        # Real fetch
        resp = requests.get(url, headers=headers, timeout=3)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            # The table usually has class 'tablesorter' or similar.
            # We want the LATEST gallop (first row usually).
            # Look for 800, 1000, 1200 columns.
            
            # Simple heuristic: Get text of first row of data
            table = soup.find('table') 
            if table:
                rows = table.find_all('tr')
                # Skip header
                for r in rows:
                    if r.find('td'):
                        # Found data row
                        # Format: Date | City | Track | Distance | Time | ...
                        cols = [clean_text(td.get_text()) for td in r.find_all('td')]
                        if len(cols) > 4:
                            return f"{cols[0]} - {cols[3]}m: {cols[4]}" # Date - Dist: Time
            return "No Gallops Found"
    except:
        pass
    return "Fetch Failed"

def scrape_program(target_date=None, target_city=None):
    if not target_date:
        # Default to tomorrow
        target_date = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
    
    print(f"Fetching Program for {target_date}...")
    
    # 1. Main Program Page
    content = get_program_page(target_date)
    if not content:
        print("Failed to load main program page.")
        return

    # 2. Get Cities
    cities = parse_program_city_links(content)
    print(f"Cities found: {[c['name'] for c in cities]}")
    
    # 3. Filter City if requested
    if target_city:
        cities = [c for c in cities if target_city.lower() in c['name'].lower()]
        
    if not cities:
        print(f"No matching cities found for {target_city}. (Check if program exists for this date)")
        return
        
    for city in cities:
        print(f"Scraping program for {city['name']}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        try:
            resp = requests.get(city['url'], headers=headers)
            if resp.status_code == 200:
                parse_program_details(resp.text, target_date, city['name'])
            else:
                print(f"Failed to fetch {city['name']}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    init_program_db()
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Date in DD/MM/YYYY format")
    parser.add_argument("--city", help="Filter by city name (e.g., İzmir)")
    args = parser.parse_args()
    
    scrape_program(args.date, args.city)
