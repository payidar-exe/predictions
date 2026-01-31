"""
Fast Turkey-Only Scraper with HP
Filters out international races and uses concurrent requests
"""
import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime, timedelta
import concurrent.futures
import time
import argparse
import re

DB_NAME = "tjk_races.db"

# Turkish cities pattern
TR_CITIES = ['İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Adana', 'Şanlıurfa', 
             'Kocaeli', 'Antalya', 'Elazığ', 'Diyarbakır']

def is_turkish_city(city_name):
    for tr in TR_CITIES:
        if tr in city_name:
            return True
    return False

def clean_text(text):
    if text:
        return text.strip().replace('\n', '').replace('\r', '').replace('  ', '')
    return None

def get_page_content(date_str):
    url = f"https://www.tjk.org/TR/YarisSever/Info/Page/GunlukYarisSonuclari?QueryParameter_Tarih={date_str}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
        return None
    except:
        return None

def parse_city_links(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    city_links = []
    tabs = soup.find('ul', class_='gunluk-tabs')
    if tabs:
        for a in tabs.find_all('a'):
            href = a.get('href')
            city_name = a.get_text(strip=True)
            if href and is_turkish_city(city_name):  # FILTER: Turkey only
                city_links.append({'name': city_name, 'url': "https://www.tjk.org" + href})
    return city_links

def parse_race_results(html_content, date_str, city_name, conn):
    """Parse and save race results with HP"""
    soup = BeautifulSoup(html_content, 'html.parser')
    race_containers = soup.select('div.races-panes > div[sehir]')
    c = conn.cursor()
    
    for race_div in race_containers:
        try:
            # Race No
            race_no_tag = race_div.select_one('h3.race-no a')
            race_no = 0
            if race_no_tag:
                race_text = race_no_tag.get_text(strip=True)
                try:
                    race_no = int(race_text.split('.')[0])
                except: pass
            
            # Config
            config_tag = race_div.select_one('h3.race-config')
            distance, track_type = "", ""
            if config_tag:
                config_text = config_tag.get_text(" ", strip=True)
                dist_match = re.search(r'(\d{4})\s+(Kum|Çim|Sentetik)', config_text, re.IGNORECASE)
                if dist_match:
                    distance = dist_match.group(1)
                    track_type = dist_match.group(2)
                else:
                    if "Kum" in config_text: track_type = "Kum"
                    elif "Çim" in config_text: track_type = "Çim"
            
            # Prize
            prize = "0"
            prize_tag = race_div.find('dl')
            if prize_tag:
                first_dd = prize_tag.find('dd')
                if first_dd:
                    prize = clean_text(first_dd.get_text())
            
            # Track condition
            track_condition = ""
            cond_span = race_div.find_parent().select_one('span.raceWeatherBrown')
            if cond_span:
                track_condition = clean_text(cond_span.get_text())
            
            # Save Race
            c.execute('''INSERT INTO races (date, city, race_no, distance, track_type, prize, track_condition)
                VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                (date_str, city_name, race_no, distance, track_type, prize, track_condition))
            race_id = c.lastrowid
            
            # Results
            table = race_div.select_one('table.tablesorter tbody')
            if not table: continue
            
            for row in table.find_all('tr'):
                cols = row.find_all('td')
                if not cols: continue
                try:
                    rank_el = row.select_one('.gunluk-GunlukYarisSonuclari-SONUCNO')
                    rank = int(clean_text(rank_el.get_text())) if rank_el else 0
                    
                    horse_tag = row.select_one('.gunluk-GunlukYarisSonuclari-AtAdi3 a')
                    horse_name = clean_text(horse_tag.get_text()).split('(')[0].strip() if horse_tag else ""
                    
                    age = clean_text(row.select_one('.gunluk-GunlukYarisSonuclari-Yas').get_text()) or ""
                    
                    weight_text = clean_text(row.select_one('.gunluk-GunlukYarisSonuclari-Kilo').get_text()) or "0"
                    try: weight = float(weight_text.split()[0].replace(',', '.'))
                    except: weight = 0.0
                    
                    jockey = clean_text(row.select_one('.gunluk-GunlukYarisSonuclari-JokeAdi').get_text()) or ""
                    owner = clean_text(row.select_one('.gunluk-GunlukYarisSonuclari-SahipAdi').get_text()) or ""
                    trainer = clean_text(row.select_one('.gunluk-GunlukYarisSonuclari-AntronorAdi').get_text()) or ""
                    time_val = clean_text(row.select_one('.gunluk-GunlukYarisSonuclari-Derece').get_text()) or ""
                    
                    ganyan_text = clean_text(row.select_one('.gunluk-GunlukYarisSonuclari-Gny').get_text()) or "0"
                    try: ganyan = float(ganyan_text.replace(',', '.'))
                    except: ganyan = 0.0
                    
                    # HP
                    hp = 0
                    hp_cell = row.select_one('.gunluk-GunlukYarisSonuclari-Hc')
                    if hp_cell:
                        hp_text = clean_text(hp_cell.get_text())
                        try: hp = int(hp_text) if hp_text and hp_text.isdigit() else 0
                        except: hp = 0
                    
                    c.execute('''INSERT INTO results (race_id, rank, horse_name, age, sire, dam, weight, jockey, owner, trainer, time, ganyan, hp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (race_id, rank, horse_name, "", "", "", weight, jockey, owner, trainer, time_val, ganyan, hp))
                except Exception as e:
                    continue
        except:
            continue
    
    conn.commit()
    return len(race_containers)

def scrape_day(date_str, conn):
    """Scrape one day, Turkey only"""
    html = get_page_content(date_str)
    if not html:
        return 0
    
    cities = parse_city_links(html)
    if not cities:
        return 0
    
    total = 0
    headers = {'User-Agent': 'Mozilla/5.0'}
    for city in cities:
        try:
            resp = requests.get(city['url'], headers=headers, timeout=10)
            if resp.status_code == 200:
                n = parse_race_results(resp.text, date_str, city['name'], conn)
                total += n
        except:
            continue
    return total

def fast_scrape(start_date_str, days):
    """Fast scrape with minimal delays"""
    start = datetime.strptime(start_date_str, "%d/%m/%Y")
    conn = sqlite3.connect(DB_NAME)
    
    print(f"FAST Turkey-Only Scrape: {days} days from {start_date_str}")
    
    for i in range(days):
        d = start + timedelta(days=i)
        ds = d.strftime("%d/%m/%Y")
        n = scrape_day(ds, conn)
        print(f"[{i+1}/{days}] {ds}: {n} races")
        time.sleep(0.3)  # Minimal delay
    
    conn.close()
    print("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_date", required=True)
    parser.add_argument("--days", type=int, default=100)
    args = parser.parse_args()
    fast_scrape(args.start_date, args.days)
