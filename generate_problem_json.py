#!/usr/bin/env python3
"""
Generate JSON election data for councils listed in problem_councils.txt.
The script reads the corresponding .txt files (e.g. Sutton_London_Borough_Council_election.txt), parses ward results and writes JSON files matching the naming convention used by extract_elections.py.
"""

import json, os, re
from pathlib import Path

BASE_DIR = Path(__file__).parent
PROBLEM_LIST = BASE_DIR / "problem_councils.txt"


def parse_txt(txt_path: Path) -> dict:
    """Parse a council txt file into a ward‑>list of candidate dicts.

    The format is similar to the example in prompt.txt:
    * A line containing only the ward name.
    * A header line (contains "Party" etc).
    * Rows with tab separators: [empty?] Party Candidate Votes …
    * Optional lines such as "Turnout" or "Registered electors" are ignored.
    """
    data: dict[str, list[dict]] = {}

    with txt_path.open(encoding="utf-8") as f:
        lines = [l.rstrip("\n") for l in f]

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        # Detect ward header: line without tabs and not a known marker
        if "\t" not in line and line.lower() not in {"turnout", "registered electors"}:
            ward = line
            # Skip header line if present
            i += 1
            if i < len(lines) and "\t" in lines[i]:
                # header line
                i += 1
            # Process rows until next ward or end
            while i < len(lines):
                row = lines[i]
                if not row.strip():
                    i += 1
                    continue
                if "\t" not in row:
                    # likely next ward
                    break
                parts = [p.strip() for p in row.split("\t") if p.strip()]
                # parts[0] could be party, parts[1] candidate, parts[2] votes
                if len(parts) < 3:
                    i += 1
                    continue
                marker = parts[0].lower()
                if marker in {"turnout", "registered electors"}:
                    i += 1
                    continue
                party = parts[0]
                candidate = parts[1].rstrip("*")
                votes_str = parts[2].replace(",", "")
                try:
                    votes = int(re.search(r"\d+", votes_str).group())
                except Exception:
                    i += 1
                    continue
                data.setdefault(ward, []).append({"candidate": candidate, "party": party, "votes": votes})
                i += 1
            continue
        i += 1
    return data


def main():
    if not PROBLEM_LIST.exists():
        print("problem_councils.txt missing")
        return
    councils = [l.strip().replace('.txt','') for l in PROBLEM_LIST.read_text().splitlines() if l.strip()]
    for council in councils:
        txt_name = f"{council}.txt"
        txt_path = BASE_DIR / txt_name
        if not txt_path.exists():
            print(f"Missing txt for {council}")
            continue
        data = parse_txt(txt_path)
        if not data:
            print(f"No data parsed for {council}")
            continue
        json_name = f"{council}_London_Borough_Council_election.json"
        json_path = BASE_DIR / json_name
        json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"Wrote {json_name}")

if __name__ == "__main__":
    main()
