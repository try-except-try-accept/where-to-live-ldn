#!/usr/bin/env python3
import os
from urllib.parse import quote

def get_council_name(line):
    return line.strip()

def get_council_filename(council_name):
    filename = council_name.lower().replace(' ', '_')
    return filename + '.html'

councils_file = '/Users/chris/GitHub/where-to-live-ldn/councils.txt'
output_dir = '/Users/chris/GitHub/where-to-live-ldn/council_results'

os.makedirs(output_dir, exist_ok=True)

with open(councils_file, 'r') as f:
    lines = [line.strip() for line in f.readlines()]

councils = [line for line in lines if line][:135]

print(f"Processing {len(councils)} councils...")
results = []

for i, council_name in enumerate(councils, 1):
    filename = get_council_filename(council_name)
    
    print(f"[{i}/{len(councils)}] {council_name} -> {filename}")
    
    results.append({
        'id': i,
        'council': council_name,
        'filename': filename
    })

print()
print("="*70)
print(f"Total: {len(councils)} councils to process")
print("="*70)
