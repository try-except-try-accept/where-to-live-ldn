#!/usr/bin/env python3
"""Download council election result pages."""

import os
import re
from pathlib import Path
import requests


COUNCILS_FILE = "/Users/chris/GitHub/where-to-live-ldn/councils.txt"
OUTPUT_DIR = Path("/Users/chris/GitHub/where-to-live-ldn/council_results")

URL_PATTERNS = [
    "/elections",
    "/local-elections",
    "/councillors-and-meetings/elections",
    "/about-elections",
    "/your-council/elections",
    "/ democracy/elections",
    "/democracy-and-elections/elections",
    "/election-results",
    "/past-election-results",
    "/local-government-and-elections/elections",
]

RELEVANT_PATTERNS = [
    re.compile(r'ward', re.I),
    re.compile(r'party', re.I),
    re.compile(r'vote.*%|\d+%.*vote', re.I),
    re.compile(r'total.*vote', re.I),
    re.compile(r'candidate', re.I),
    re.compile(r'election.*result', re.I),
]


def read_councils(filepath):
    """Read councils from file."""
    councils = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if ':' in line:
                parts = line.split(':', 1)
                councils.append(parts[1].strip())
            elif line:
                councils.append(line)
    return councils


def normalize_name(name):
    """Normalize council name for URL."""
    name = name.lower()
    name = name.replace(' and ', '_and_')
    name = name.replace(' ', '-')
    return name


def download_council(council_name, index, total):
    """Try to download election page for a council."""
    print(f"[{index}/{total}] {council_name}", flush=True)
    
    normalized = normalize_name(council_name)
    
    for pattern in URL_PATTERNS:
        url = f"https://www.{normalized}.gov.uk{pattern}"
        
        try:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                continue
            
            content_lower = response.text.lower()
            
            has_relevant_content = any(pattern.search(content_lower) for pattern in RELEVANT_PATTERNS)
            
            if has_relevant_content:
                output_path = OUTPUT_DIR / f"{normalized}.html"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                return True
                
        except requests.RequestException:
            continue
    
    return False


def main():
    """Main entry point."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    councils = read_councils(COUNCILS_FILE)
    total = len(councils)
    
    downloaded = sum(1 for f in OUTPUT_DIR.glob("*.html") if not f.name.endswith('.json'))
    print(f"Already downloaded: {downloaded}", flush=True)
    print(f"Total councils: {total}", flush=True)
    
    for i, council in enumerate(councils, 1):
        normalized = normalize_name(council)
        output_path = OUTPUT_DIR / f"{normalized}.html"
        
        if output_path.exists():
            continue
        
        download_council(council, i, total)


if __name__ == "__main__":
    main()
