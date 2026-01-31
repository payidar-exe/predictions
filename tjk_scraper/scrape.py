import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import sqlite3
from datetime import datetime, timedelta

# Setup database
DB_NAME = "tjk_races.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Create tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS races (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            city TEXT,
            race_no INTEGER,
            distance TEXT,
            track_type TEXT,
            prize TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            race_id INTEGER,
            rank INTEGER,
            horse_name TEXT,
            age TEXT,
            sire TEXT,
            dam TEXT,
            weight REAL,
            jockey TEXT,
            owner TEXT,
            trainer TEXT,
            time TEXT,
            ganyan REAL,
            FOREIGN KEY(race_id) REFERENCES races(id)
        )
    ''')
    conn.commit()
    conn.close()

def get_page_content(date_str):
    url = f"https://www.tjk.org/TR/YarisSever/Info/Page/GunlukYarisSonuclari?QueryParameter_Tarih={date_str}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'https://www.tjk.org/TR/YarisSonuclari',
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to fetch {date_str}: Status {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching {date_str}: {e}")
        return None

def parse_city_links(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    city_links = []
    
    # Extract links from the city tabs
    tabs = soup.find('ul', class_='gunluk-tabs')
    if tabs:
        for a in tabs.find_all('a'):
            href = a.get('href')
            city_name = a.get_text(strip=True)
            if href:
                city_links.append({'name': city_name, 'url': "https://www.tjk.org" + href})
    
    return city_links

def clean_text(text):
    if text:
        return text.strip().replace('\n', '').replace('\r', '').replace('  ', '')
    return None

def parse_race_results(html_content, date_str, city_name):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Each race is typically in a separate div or the tables are listed sequentially.
    # Based on the structure: <div class="races-panes"> -> <div id="12345" sehir="Bursa">
    race_containers = soup.select('div.races-panes > div[sehir]')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    print(f"Found {len(race_containers)} races for {city_name} on {date_str}")
    
    for race_div in race_containers:
        try:
            # --- Extract Race Info ---
            race_no_tag = race_div.select_one('h3.race-no a')
            race_no = 0
            if race_no_tag:
                race_text = race_no_tag.get_text(strip=True)
                # Example: "1. Koşu13.00" -> extract "1"
                try:
                    race_no = int(race_text.split('.')[0])
                except:
                    pass
            
            # Race Config (Distance, Track, etc.)
            # The config text is mixed in text nodes and links within h3.race-config
            # Example: "ŞARTLI 2 /X, 3 Yaşlı İngilizler, 58 kg, 1400 Kum"
            config_tag = race_div.select_one('h3.race-config')
            distance = ""
            track_type = ""
            if config_tag:
                config_text = config_tag.get_text(" ", strip=True) 
                # Very rough extraction: look for numbers like 1200, 1400, 2000
                import re
                dist_match = re.search(r'(\d{4})\s+(Kum|Çim|Sentetik)', config_text, re.IGNORECASE)
                if dist_match:
                    distance = dist_match.group(1)
                    track_type = dist_match.group(2)
                else:
                    # Fallback if text format differs
                    if "Kum" in config_text: track_type = "Kum"
                    elif "Çim" in config_text: track_type = "Çim"
                    
            # Prize (1st place)
            prize = "0"
            prize_tag = race_div.find('dl')
            if prize_tag:
                first_prize_dd = prize_tag.find('dd')
                if first_prize_dd:
                    prize = clean_text(first_prize_dd.get_text())
            
            # PHASE 6: Track Condition (Kum: Sulu / Kum: Normal)
            # Look for condition info in the race container or parent
            track_condition = ""
            cond_span = race_div.find_parent().select_one('span.raceWeatherBrown')
            if cond_span:
                track_condition = clean_text(cond_span.get_text())
            
            # Save Race (with track_condition)
            c.execute('''
                INSERT INTO races (date, city, race_no, distance, track_type, prize, track_condition)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (date_str, city_name, race_no, distance, track_type, prize, track_condition))
            race_id = c.lastrowid
            
            # --- Extract Results ---
            table = race_div.select_one('table.tablesorter tbody')
            if not table:
                continue
            
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if not cols: continue
                
                # Check class names if possible for robust parsing, or rely on index
                # 0: Forma, 1: S (Rank), 2: At İsmi, 3: Yaş, 4: Baba-Anne, 5: Kilo, 6: Jokey, 7: Sahip, 8: Ant, 9: Derece, 10: Gny, ...
                
                try:
                    # Rank
                    rank_text = clean_text(row.select_one('.gunluk-GunlukYarisSonuclari-SONUCNO').get_text())
                    rank = int(rank_text) if rank_text and rank_text.isdigit() else 0
                    
                    # Horse Name
                    horse_tag = row.select_one('.gunluk-GunlukYarisSonuclari-AtAdi3 a')
                    horse_name = clean_text(horse_tag.get_text()) if horse_tag else "Unknown"
                    # Remove suffixes like (5) or KG DB if mixed (soup usually separates tags but text might have it)
                    horse_name = horse_name.split('(')[0].strip() 
                    
                    # Age
                    age = clean_text(row.select_one('.gunluk-GunlukYarisSonuclari-Yas').get_text())
                    
                    # Sire/Dam
                    sire = ""
                    dam = ""
                    origin_cell = row.select_one('.gunluk-GunlukYarisSonuclari-Baba')
                    if origin_cell:
                        origin_links = origin_cell.find_all('a')
                        if len(origin_links) >= 1: sire = clean_text(origin_links[0].get_text())
                        if len(origin_links) >= 2: dam = clean_text(origin_links[1].get_text())
                        
                    # Weight
                    weight_text = clean_text(row.select_one('.gunluk-GunlukYarisSonuclari-Kilo').get_text())
                    try:
                        weight = float(weight_text.split()[0].replace(',', '.'))
                    except:
                        weight = 0.0
                        
                    # Jokey
                    jockey = clean_text(row.select_one('.gunluk-GunlukYarisSonuclari-JokeAdi').get_text())
                    
                    # Sahip
                    owner = clean_text(row.select_one('.gunluk-GunlukYarisSonuclari-SahipAdi').get_text())
                    
                    # Antrenor
                    trainer = clean_text(row.select_one('.gunluk-GunlukYarisSonuclari-AntronorAdi').get_text())
                    
                    # Time (Derece)
                    time_val = clean_text(row.select_one('.gunluk-GunlukYarisSonuclari-Derece').get_text())
                    
                    # Ganyan
                    ganyan_text = clean_text(row.select_one('.gunluk-GunlukYarisSonuclari-Gny').get_text())
                    try:
                        ganyan = float(ganyan_text.replace(',', '.'))
                    except:
                        ganyan = 0.0
                    
                    # PHASE 6: HP (Handicap Points)
                    hp = 0
                    hp_cell = row.select_one('.gunluk-GunlukYarisSonuclari-Hc')
                    if hp_cell:
                        hp_text = clean_text(hp_cell.get_text())
                        try:
                            hp = int(hp_text) if hp_text and hp_text.isdigit() else 0
                        except:
                            hp = 0

                    c.execute('''
                        INSERT INTO results (race_id, rank, horse_name, age, sire, dam, weight, jockey, owner, trainer, time, ganyan, hp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (race_id, rank, horse_name, age, sire, dam, weight, jockey, owner, trainer, time_val, ganyan, hp))
                    
                except Exception as e:
                    print(f"Error parse row: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error parse race: {e}")
    
    conn.commit()
    conn.close()

def scrape_range(start_date, days=1):
    start = datetime.strptime(start_date, "%d/%m/%Y")
    
    for i in range(days):
        current = start + timedelta(days=i)
        date_str = current.strftime("%d/%m/%Y")
        print(f"Scraping {date_str}...")
        
        # 1. Get Main Page
        content = get_page_content(date_str)
        if not content:
            continue
            
        # 2. Extract City specific URLs
        cities = parse_city_links(content)
        print(f"Found {len(cities)} cities for {date_str}: {[c['name'] for c in cities]}")
        
        # 3. Process each city
        for city in cities:
            print(f"Fetching details for {city['name']}...")
            
            # Avoid fetching international races if user only wants TJK (Turkish)
            # Generally, foreign races have country suffixes like 'ABD', 'Birleşik Krallık'.
            # Let's scrape everything for now or filter if requested. 
            # User said "TJK'yı scrape edebiliriz" -> imply all TJK data.
            
            try:
                # Need to use the same session or headers to mimick browser?
                # The URLs are direct, so requests should work if not blocked.
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'X-Requested-With': 'XMLHttpRequest'
                }
                resp = requests.get(city['url'], headers=headers)
                if resp.status_code == 200:
                    parse_race_results(resp.text, date_str, city['name'])
                    time.sleep(1) # Gentle delay between cities
                else:
                    print(f"Failed to fetch {city['name']}: {resp.status_code}")
                    
            except Exception as e:
                print(f"Error fetching {city['name']}: {e}")
        
        time.sleep(2) # Delay between days

if __name__ == "__main__":
    import argparse
    init_db()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_date", default="01/01/2024", help="Start date DD/MM/YYYY")
    parser.add_argument("--days", type=int, default=1, help="Number of days to scrape")
    args = parser.parse_args()
    
    scrape_range(args.start_date, args.days)
