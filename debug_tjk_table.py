import requests
from bs4 import BeautifulSoup

def debug_horse(horse_id):
    url = f"https://www.tjk.org/TR/YarisSever/Query/Page/IdmanIstatistikleri?QueryParameter_AtId={horse_id}"
    print(f"Fetching {url}...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables.")
    
    for i, t in enumerate(tables):
        print(f"\n--- TABLE {i} ---")
        
        # Check header
        thead = t.find('thead')
        if thead:
            headers = [th.get_text().strip() for th in thead.find_all(['th', 'td'])]
            print(f"Header: {headers}")
        else:
            # Maybe first row?
            first_row = t.find('tr')
            if first_row:
                headers = [td.get_text().strip() for td in first_row.find_all(['th', 'td'])]
                print(f"First Row (Header?): {headers}")
        
        # Print first 2 data rows
        rows = t.find_all('tr')
        d_count = 0
        for r in rows:
            cols = [td.get_text().strip() for td in r.find_all('td')]
            if len(cols) > 0:
                print(f"Row {d_count}: {cols}")
                d_count += 1
                if d_count >= 2: break

debug_horse(109601)
