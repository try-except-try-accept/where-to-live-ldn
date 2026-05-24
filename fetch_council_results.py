#!/usr/bin/env python3
"""
Fetch council election results for May 2026 and extract to JSON.
Validates pages contain ward names, parties (like "Reform UK"), and percentage figures.
"""
import os
import re
import json
import time

def is_valid_results_page(html_content):
    """Check if page contains ward names, parties, and percentages"""
    patterns = [
        (r'ward', ' Ward'),
        (r'reform\s+uk|reform.*party', 'Reform UK'),
        (r'\b\d+%.*vot|vot.*\d+%', 'percentage with vote'),
        (r'conservative|labour|liberal\s+democrat', 'major party'),
        (r'\d+\s+vot|\bvote\b.*\d+', 'vote count'),
    ]
    
    found = []
    for pattern, desc in patterns:
        if re.search(pattern, html_content, re.IGNORECASE):
            found.append(desc)
    
    # Must have at least 3 indicators
    return len(found) >= 3, found

def extract_ward_data(html_content):
    """Extract ward-level voting data from HTML"""
    wards = []
    
    # Look for ward sections - common patterns
    ward_sections = re.split(r'ward|Ward|h2.* Ward', html_content, flags=re.IGNORECASE)
    
    for section in ward_sections[1:]:  # Skip first non-ward part
        ward_data = extract_single_ward(section)
        if ward_data:
            wards.append(ward_data)
    
    return wards

def extract_single_ward(section):
    """Extract data from a single ward section"""
    # Check if this looks like ward results
    if not any(x in section for x in ['%', 'vote', 'candidate', 'party']):
        return None
    
    # Extract ward name
    ward_match = re.search(r'(?:ward|Ward)[^<]*[^\s](\w+.*?)(?: ward| Ward|$)', section, re.IGNORECASE)
    ward_name = ward_match.group(1).strip() if ward_match else None
    
    # Extract candidates with vote counts and percentages
    candidates = []
    
    # Pattern for candidate: Name Partyname followed by votes/percentage
    candidate_patterns = [
        r'([^<>\n]+?)\s*\[.*?\]\s*([A-Za-z\s]+?(?:Party|UK|Independent|Conservative|Labour|Liberal))\s*(\d+)\s*\(\s*(\d+)%',
        r'([A-Za-z\s]+?(?:Party|UK|Independent|Conservative|Labour|Liberal))\s*(\d+)\s*\(\s*(\d+)%',
        r'([A-Za-z\s,]+?)\s+(Conservative|Labour|Reform UK|Liberal Democrat|Green|Independent)\s+(\d+)\s*\(\s*(\d+)%',
    ]
    
    for pattern in candidate_patterns:
        matches = re.findall(pattern, section, re.IGNORECASE)
        if matches:
            for match in matches:
                if len(match) >= 3:
                    name = match[0].strip() if isinstance(match[0], str) else ''
                    party = match[1] if len(match) > 1 and isinstance(match[1], str) else ''
                    try:
                        votes = int(match[-2]) if len(match) >= 3 else 0
                        pct = int(match[-1]) if len(match) >= 3 else 0
                    except:
                        votes, pct = 0, 0
                    
                    candidates.append({
                        'name': name,
                        'party': party.strip(),
                        'votes': votes,
                        'percentage': pct
                    })
    
    # Extract turnout percentage
    turnout_match = re.search(r'turnout[:\s]*\d+\.?\d*%', section, re.IGNORECASE)
    turnout = None
    if turnout_match:
        turnout_match2 = re.search(r'(\d+\.?\d*)%', turnout_match.group(0))
        if turnout_match2:
            turnout = float(turnout_match2.group(1))
    
    # Extract total votes if available
    total_votes_match = re.search(r'total\s+vot(?:e)?s[:\s]*(\d+)', section, re.IGNORECASE)
    total_votes = int(total_votes_match.group(1)) if total_votes_match else None
    
    if candidates or turnout:
        return {
            'ward': ward_name,
            'candidates': candidates[:5],
            'turnout_percentage': turnout,
            'total_votes': total_votes
        }
    
    return None

def download_council_page(council_name, timeout=10):
    """Download council elections page"""
    base_names = [
        f"https://www.{council_name.replace(' ', '').lower()}.gov.uk",
        f"https://www.{council_name.lower().replace(' ', '-')}.gov.uk",
    ]
    
    suffixes = ['/elections', '/voting-and-elections', '/local-elections', 
                '/election-results', '/council-and-democracy/elections',
                '/democracy/elections']
    
    for base in base_names:
        for suffix in suffixes:
            url = base + suffix
            print(f"  Trying: {url}")
            
            cmd = f'''curl -sL -H "User-Agent: Mozilla/5.0" "{url}"'''
            result = os.popen(cmd).read()
            
            if result and len(result) > 100:
                is_valid, indicators = is_valid_results_page(result)
                if is_valid:
                    print(f"  VALID results page found! Indicators: {indicators}")
                    return result, url
                elif len(result) > 1000:
                    print(f"  Got page but validation failed. Size: {len(result)}, Indicators: {indicators}")
    
    return None, None

def main():
    councils = ["Brentwood", "Dudley", "Gateshead", "Lincoln", "Rochdale"]
    
    results_dir = "/Users/chris/GitHub/where-to-live-ldn/council_results"
    os.makedirs(results_dir, exist_ok=True)
    
    all_data = {}
    
    for council in councils:
        print(f"\n=== {council} ===")
        
        html, url = download_council_page(council)
        
        if not html:
            print(f"  No page found")
            all_data[council] = {'status': 'no_page', 'url': None}
            continue
        
        filename = f"{council.replace(' ', '_').lower()}.html"
        filepath = os.path.join(results_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(html)
        print(f"  Saved: {filename}")
        
        is_valid, indicators = is_valid_results_page(html)
        
        if not is_valid:
            print(f"  NOT a valid results page. Indicators: {indicators}")
            all_data[council] = {'status': 'invalid_page', 'url': url, 'indicators': indicators}
            continue
        
        ward_data = extract_ward_data(html)
        
        council_result = {
            'council': council,
            'url': url,
            'ward_results': ward_data
        }
        
        json_path = os.path.join(results_dir, f"{council.replace(' ', '_').lower()}.json")
        with open(json_path, 'w') as f:
            json.dump(council_result, f, indent=2)
        print(f"  Saved JSON with {len(ward_data)} wards")
        
        all_data[council] = {
            'status': 'success',
            'url': url,
            'wards_found': len(ward_data),
            'has_reform_uk': any('Reform UK' in str(w) for w in ward_data),
            'has_percentages': any(w.get('turnout_percentage') for w in ward_data)
        }
        
        time.sleep(1)
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    
    for council, data in all_data.items():
        status = f"✓ {data['status']}" if data['status'] == 'success' else f"✗ {data['status']}"
        print(f"{council}: {status}")
    
    return all_data

if __name__ == "__main__":
    main()
