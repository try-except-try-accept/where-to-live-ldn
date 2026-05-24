#!/usr/bin/env python3
"""
Script to extract 2026 UK council election voting data from Wikipedia.
The script reads councils.txt, attempts to fetch a page for each council
in the form 2026_{CouncilName}_Borough_Council_election, parses all
tables that follow a ward heading and extracts candidate name, party and
vote count. The results are written to elections_data.json.
"""

import json
import random
import re
from pathlib import Path

import curl_cffi.requests
from bs4 import BeautifulSoup

BASE_URL = "https://en.wikipedia.org/wiki/"
COUNCILS_FILE = Path("london_councils.txt")

# Helper to build page title from council name
def wiki_title(council: str) -> str:
    """Return the Wikipedia page title for a London council."""
    name = council.replace(" ", "_")
    return f"2026_{name}_London_Borough_Council_election"

# Fetch a URL with curl_cffi, using browser impersonation to avoid blocking
def fetch(url: str) -> tuple[str, int]:
    """Download a URL with curl_cffi and return (body, status)."""
    headers = {
        "User-Agent": random.choice(
            [
                # Chrome 115
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                # Firefox 115
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
                # Safari 17
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            ]
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        # Impersonate a modern browser to avoid blocking
        resp = curl_cffi.requests.get(url, headers=headers, timeout=10, impersonate="chrome")
        return resp.text, resp.status_code
    except Exception as e:
        print(f"Network error fetching {url}: {e}")
        return "", 0

# Parse a single council page
def parse_council_page(body: str) -> dict:
    soup = BeautifulSoup(body, "html.parser")

    data: dict[str, list[dict]] = {}
    # Find all headings that likely denote ward names (h2/h3)
    for heading in soup.find_all(re.compile("^h[23]")):
        ward = heading.get_text(strip=True)
        # Find next table after this heading
        table = heading.find_next("table", class_="wikitable")
        if not table:
            continue
        rows = table.find_all("tr")
        # Skip header row
        for tr in rows[1:]:
            cols = tr.find_all("td")
            if len(cols) < 3:
                continue
            # Order is: Party, Candidate, Votes (or similar)
            party = cols[0].get_text(strip=True).strip()
            candidate = cols[1].get_text(strip=True)
            votes_raw = cols[-1].get_text(strip=True).replace(",", "")
            try:
                votes = int(votes_raw)
            except ValueError:
                continue
            data.setdefault(ward, []).append({
                "candidate": candidate,
                "party": party,
                "votes": votes,
            })
    return data

if __name__ == "__main__":
    councils = [line.strip() for line in COUNCILS_FILE.read_text().splitlines() if line.strip()]
    for council in councils:
        title = wiki_title(council)
        url = BASE_URL + title
        print(f"Processing {council} → {url}")
        body, status = fetch(url)
        if status != 200:
            print(f"Failed to fetch {url} (status {status})")
            alt = input(f"Enter alternate URL for '{council}' (or leave blank to skip): ")
            if alt.strip():
                alt_body, _ = fetch(alt)
                safe_name = re.sub(r"\W+", "_", council)
                Path(f"{safe_name}_missing.html").write_text(alt_body, encoding="utf-8")
                print(f"Saved raw HTML to {safe_name}_missing.html")
            continue
        council_data = parse_council_page(body)
        if council_data:
            safe_name = re.sub(r"\W+", "_", council)
            file_name = f"{safe_name}_London_Borough_Council_election.json"
            Path(file_name).write_text(json.dumps(council_data, indent=2), encoding="utf-8")
            print(f"Data written to {file_name}")
        else:
            print(f"No ward tables found in {url}")
