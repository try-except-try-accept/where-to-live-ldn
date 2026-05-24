#!/usr/bin/env python3
import os
import re
import time
import subprocess

def is_valid_results_page(html_content):
    """Check if page contains ward names, parties, and vote counts"""
    patterns = [
        (r'ward', 'Ward'),
        (r'reform\s+uk|reform.*party', 'Reform UK'),
        (r'\b\d+%.*vot|vot.*\d+%', 'percentage with vote'),
        (r'conservative|labour|liberal\s+democrat', 'major party'),
        (r'\d+\s+vot|\bvote\b.*\d+', 'vote count'),
        (r'green.*party|green\s+party', 'Green Party'),
    ]
    
    found = []
    for pattern, desc in patterns:
        if re.search(pattern, html_content, re.IGNORECASE):
            found.append(desc)
    
    return len(found) >= 3, found

def get_council_url(council_name):
    """Generate potential URLs for council election results"""
    base_names = [
        f"https://www.{council_name.replace(' ', '').lower()}.gov.uk",
        f"https://www.{council_name.lower().replace(' ', '-')}.gov.uk",
    ]
    
    suffixes = [
        '/elections',
        '/voting-and-elections',
        '/local-elections',
        '/election-results',
        '/council-and-democracy/elections',
        '/democracy/elections',
        '/your-council/elections',
    ]
    
    elections_2026_paths = [
        '/2026/elections',
        '/elections/2026',
        '/local-elections-2026',
        '/mayor-and-council-elections',
    ]
    
    all_urls = []
    for base in base_names:
        for suffix in suffixes:
            all_urls.append(base + suffix)
        for path in elections_2026_paths:
            all_urls.append(base + path)
    
    return all_urls

def download_page(url):
    """Download a web page using curl"""
    try:
        cmd = ['curl', '-sL', '--insecure', '-H', 'User-Agent: Mozilla/5.0', url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.stdout and len(result.stdout) > 100:
            return result.stdout
    except Exception as e:
        pass
    return None

def download_council_page(council_name, output_dir):
    """Download council elections page with validation"""
    urls = get_council_url(council_name)
    
    print(f"\nProcessing: {council_name}")
    
    for url in urls:
        html = download_page(url)
        
        if not html:
            continue
        
        is_valid, indicators = is_valid_results_page(html)
        
        if is_valid:
            filename = f"{council_name.replace(' ', '_').lower()}.html"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(html)
            
            print(f"  VALID results page found!")
            print(f"    URL: {url}")
            print(f"    Saved: {filename}")
            print(f"    Indicators: {', '.join(indicators)}")
            
            return {'status': 'success', 'url': url, 'indicators': indicators}
        
        elif len(html) > 500:
            print(f"  - Page found but not valid yet. Trying next URL...")
    
    print(f"  No valid results page found")
    return {'status': 'not_found', 'url': None, 'indicators': []}

def main():
    councils_file = '/Users/chris/GitHub/where-to-live-ldn/councils.txt'
    output_dir = '/Users/chris/GitHub/where-to-live-ldn/council_results'
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(councils_file, 'r') as f:
        lines = [line.strip() for line in f.readlines()]
    
    existing_files = os.listdir(output_dir)
    
    councils = [line for line in lines if line and ':' not in line][:135]
    
    print(f"Processing {len(councils)} councils...")
    print(f"Output directory: {output_dir}")
    print()
    
    downloaded_count = 0
    not_found_count = 0
    
    for i, council_name in enumerate(councils, 1):
        if not council_name:
            continue
        
        filename = f"{council_name.replace(' ', '_').lower()}.html"
        
        if filename in existing_files:
            print(f"[{i}/{len(councils)}] {council_name} - Already downloaded: {filename}")
            downloaded_count += 1
            continue
        
        result = download_council_page(council_name, output_dir)
        
        if result['status'] == 'success':
            downloaded_count += 1
        else:
            not_found_count += 1
        
        time.sleep(0.5)
    
    print()
    print("="*60)
    print(f"SUMMARY: {downloaded_count} downloaded, {not_found_count} not found")
    print("="*60)

if __name__ == "__main__":
    main()
