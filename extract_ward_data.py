#!/usr/bin/env python3
"""Extract ward voting data from Hackney HTML to JSON"""
import re
import json

# Read the HTML file
with open('/Users/chris/GitHub/where-to-live-ldn/council_results/hackney.html', 'r') as f:
    html = f.read()

wards = []

# Split by ward sections
ward_pattern = r'(Brownswood|Cazenove|Clissold|Dalston|De Beauvoir|Hackney Central|Hackney Downs|Hackney Wick|Haggerston|Homerton|Hoxton East and Shoreditch|Hoxton West|King\'s Park|Lea Bridge|London Fields|Shacklewell|Springfield|Stamford Hill West|Stoke Newington|Victoria|Woodberry Down) ward'

matches = re.finditer(ward_pattern, html)
ward_names = [m.group(1) for m in matches]

print(f"Found {len(ward_names)} wards")

# Extract data for each ward
for ward_name in ward_names:
    # Find the section for this ward - escape special regex chars
    escaped_ward = re.escape(ward_name)
    pattern = f'({escaped_ward} ward)(.*?)(?=h2|div class="grid)'
    match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
    
    if not match:
        print(f"Could not find section for {ward_name}")
        continue
    
    section = match.group(2)
    
    # Extract turnout
    turnout_pct = None
    turnout_match = re.search(r'Turnout:\s*(\d+\.?\d*)%', section, re.IGNORECASE)
    if turnout_match:
        turnout_pct = float(turnout_match.group(1))
    
    # Extract candidate data
    candidates = []
    # Pattern for candidate line: Name Party Votes (Pct%)
    # Common patterns:
    # 1. "ADEJARE, SorayaGreen Party1,554Elected"
    # 2. "CASTANO, LeoReform UK138"
    
    lines = section.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for candidate patterns
        if re.search(r'[A-Z]{2,}', line) and ('Party' in line or 'Reform UK' in line):
            # Try to extract candidate info
            # Pattern: Name, SurnamePartyName votes (pct%)
            candidate_match = re.search(
                r'([A-Z][a-z]+(?:\s+[A-Za-z\'-]+)*)\s+((?:Green|Labour|Conservative|Liberal\s+Democrat|Reform\s+UK|Trade\s+Unionist|Hackney\s+Independent|Independent(?:\s+Network)?|Women\'s\s+Equality)\s*Party(?:\s+Candidate)?|(?:Independent(?:\s+Network)?)|Duma\s+Polska|Women\'s\s+Equality)',
                line,
                re.IGNORECASE
            )
            
            if candidate_match:
                name = candidate_match.group(1).strip()
                party = candidate_match.group(2).strip()
                
                # Extract votes
                votes_match = re.search(r'(\d{1,3}(?:,\d{3})*)(?:\s*\d+%)?', line)
                votes = None
                if votes_match:
                    votes_str = votes_match.group(1).replace(',', '')
                    try:
                        votes = int(votes_str)
                    except:
                        pass
                
                # Extract percentage if available
                pct_match = re.search(r'\((\d+\.?\d*)%\)', line)
                pct = None
                if pct_match:
                    try:
                        pct = float(pct_match.group(1))
                    except:
                        pass
                
                elected = 'Elected' in line
                
                candidates.append({
                    'name': name,
                    'party': party,
                    'votes': votes,
                    'percentage': pct,
                    'elected': elected
                })
        
        i += 1
    
    ward_data = {
        'ward': ward_name,
        'turnout_percentage': turnout_pct,
        'candidates': candidates
    }
    
    wards.append(ward_data)
    print(f"  {ward_name}: {len(candidates)} candidates")

# Save JSON
with open('/Users/chris/GitHub/where-to-live-ldn/council_results/hackney.json', 'w') as f:
    json.dump({
        'council': 'Hackney',
        'url': 'https://www.hackney.gov.uk/council-and-elections/elections-and-voting/election-results/local-election-results',
        'ward_results': wards
    }, f, indent=2)

print(f"\nSaved {len(wards)} wards to hackney.json")
print("\nSample ward data:")
print(json.dumps(wards[0], indent=2))
