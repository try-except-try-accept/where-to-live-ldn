import json
from os import listdir
from time import sleep
from curl_cffi import requests
with open("data.json") as f:
    data = json.load(f)
WARDS = data["wards"]

WARD_TO_ID = {}
with open("locations.json") as f:
    data = json.load(f)
    for entry in data:
        WARD_TO_ID[entry["name"]] = entry["id"]

LOCATION_API_URL = "https://data.police.uk/api/metropolitan/neighbourhoods"
CRIME_AT_LOCATION_API_URI = "https://data.police.uk/api/crimes-at-location?date=<date>&location_id=<locid>"
CRIME_AT_AREA_API_URI = "https://data.police.uk/api/crimes-street/all-crime?date=<date>&poly=<poly>"

def scrape_police_data(page):
    from bs4 import BeautifulSoup

    # Assuming 'html_content' is your page source
    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. Find all tables on the page
    tables = soup.find_all('table')

    target_table = None

    # 2. Iterate to find the one with the specific caption
    for table in tables:
        # Look for a <caption> element directly inside this table
        caption = table.find('caption', recursive=False)
        
        if caption and caption.get_text(strip=True) == "Crime types description":
            target_table = table
            break

    # 3. Extract the contents if found
    if target_table:
        print("Found the target table! Extracting data...\n")
        
        # Loop through the table rows (tr)
        for row in target_table.find_all('tr'):
            # Get all cell contents (both headers 'th' and data 'td')
            cells = [cell.get_text(strip=True) for cell in row.find_all(['th', 'td'])]
            print(cells)
    else:
        print("Table with caption 'Crime types description' not found.")


def process_all_wards(start_at=""):


    for i, ward in enumerate(WARDS):

    

        try:
            location_id = WARD_TO_ID[ward]
        except KeyError as e:
            print(e)
            continue
        print(f"processing {ward} location id {location_id}")
        ward_fn = ward.lower().replace(" ", "_")

        if ward_fn <= start_at:
            print(f"skipping {ward}")
            continue

        boundary_url = f"https://data.police.uk/api/metropolitan/{location_id}/boundary"
        bd = requests.get(boundary_url).json()
        print("Has boundaries", bd)
        poly = ":".join(e["latitude"] + "," + e["longitude"] for e in bd)


        for month in range(1, 13):
            
            
            date = f"2025-{str(month).zfill(2)}"
            print(f"accessing crime data for {date}")
            url = CRIME_AT_AREA_API_URI.replace("<date>", date).replace("<poly>", poly)
            post = False
            if len(url) >= 4094:
                post = True
                url = "https://data.police.uk/api/crimes-street/all-crime"
            print(url)

            payload = {
                "date": date,
                "poly": poly
            }
            
            try:
                if post:
                    response = requests.post(url, data=payload)
                else:
                    response = requests.get(url)
            except Exception as e:
                print(e)
                input()
                sleep(30)

            if response.status_code == 200:
                crime_data = response.json()
            else:
                print(ward, f"payload length: {len(poly)}", response)
                print("skipping ward")
                break

            try:
                with open(f"./crime/{ward_fn}.json") as f:
                    existing = json.load(f)
            except Exception as e:
                print(e)
                existing = None

            if existing is None:
                existing = []

            crime_data.extend(existing)
            with open(f"./crime/{ward_fn}.json", "w", encoding="utf-8") as f:
                json.dump(crime_data, f, indent=4, ensure_ascii=False)
        
        sleep(30)
            

def check_current_data():
    for fn in listdir("./crime"):
        if not fn.endswith("json"): continue

        with open(f"./crime/{fn}") as f:
            data = json.load(f)
            if data is None:
                continue
            print(f"{fn} : {len(data)} crimes reported")


if __name__ == "__main__":
    process_all_wards(start_at="cavendish-square-and-oxford-market")
    #check_current_data()
