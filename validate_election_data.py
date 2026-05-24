#!/usr/bin/env python3
"""Validate London borough election JSON files for data quality issues."""

import json
import re
from pathlib import Path

OUTPUT_FILE = Path("validation_report.json")

INVALID_TERMS = [
    "results", "summary", "background", "history", "election",
    "total", "majority", "turnout", "swing", "previous",
    "composition", "results summary", "ward results", "council",
]


def is_ward_name(name: str) -> bool:
    name_lower = name.lower().strip()
    for term in INVALID_TERMS:
        if term in name_lower:
            return False
    has_ward = "ward" in name_lower or "road" in name_lower or len(name_lower) > 5
    has_space = " " in name or "_" in name
    return (has_ward or has_space) and len(name_lower) >= 3


def is_valid_candidate(name: str) -> bool:
    if not name or len(name) < 2:
        return False
    name_lower = name.lower().strip()
    skip_patterns = [
        r"^majority", r"^turnout", r"^swing",
        r"^\*+$", r"^(\d+\.?\d*)$", r"^\s*$",
    ]
    for pattern in skip_patterns:
        if re.match(pattern, name_lower):
            return False
    if not re.search(r"[a-zA-Z]", name):
        return False
    if len(re.findall(r"[\*\$@#%&]", name)) > 2:
        return False
    word_count = len(name.split())
    if word_count > 4:
        return False
    return True


def is_valid_party(party: str) -> bool:
    if not party or len(party) < 2:
        return False
    party_lower = party.lower().strip()
    if any(term in party_lower for term in INVALID_TERMS):
        return False
    if not re.search(r"[a-zA-Z]", party):
        return False
    if len(re.findall(r"\d", party)) > 3:
        return False
    cleaned = re.sub(r"[\*\-–—]", "", party).strip()
    return len(cleaned) > 1


def validate_council_file(filepath: Path):
    issues = []
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        issues.append({"type": "file_error", "message": f"Failed to load JSON: {e}"})
        return {"valid": False, "issues": issues}
    
    if not isinstance(data, dict):
        return {"valid": False, "issues": [{"type": "structure_error", "message": "Expected dict at root level"}]}
    
    wards_without_data = []
    wards_with_issues = {}
    
    for ward, candidates in data.items():
        if not is_ward_name(ward):
            wards_with_issues[ward] = ["Invalid ward name format"]
        
        if not isinstance(candidates, list):
            wards_with_issues.setdefault(ward, []).append("Candidates is not a list")
            continue
        
        if len(candidates) == 0:
            wards_without_data.append(ward)
            continue
        
        ward_issues = []
        
        for i, candidate in enumerate(candidates):
            if not isinstance(candidate, dict):
                ward_issues.append(f"Candidate {i} is not a dict")
                continue
            
            if "candidate" not in candidate:
                ward_issues.append(f"Candidate {i}: Missing 'candidate' field")
            elif not is_valid_candidate(candidate["candidate"]):
                ward_issues.append(f"Candidate {i}: Malformed candidate name '{candidate['candidate']}'")
            
            if "party" not in candidate:
                ward_issues.append(f"Candidate {i}: Missing 'party' field")
            elif not is_valid_party(candidate["party"]):
                ward_issues.append(f"Candidate {i}: Malformed party '{candidate['party']}'")
            
            if "votes" not in candidate:
                ward_issues.append(f"Candidate {i}: Missing 'votes' field")
            else:
                try:
                    votes = int(candidate["votes"])
                    if votes < 0:
                        ward_issues.append(f"Candidate {i}: Negative votes ({votes})")
                except (ValueError, TypeError):
                    ward_issues.append(f"Candidate {i}: Invalid votes value '{candidate['votes']}'")
        
        if ward_issues:
            wards_with_issues[ward] = ward_issues
    
    valid = len(wards_without_data) == 0 and len(wards_with_issues) == 0
    
    return {
        "valid": valid,
        "total_wards": len(data),
        "wards_without_data": wards_without_data,
        "wards_with_issues": wards_with_issues,
    }


def main():
    json_files = sorted(Path(".").glob("*_London_Borough_Council_election.json"))
    
    if not json_files:
        print("No election JSON files found!")
        return
    
    results = {}
    
    for filepath in json_files:
        print(f"Validating {filepath}...", end=" ")
        result = validate_council_file(filepath)
        results[filepath.name] = result
        status = "OK" if result["valid"] else "ISSUES"
        print(status)
        
        if not result["valid"]:
            print(f"  - {filepath.name}:")
            for ward, issues in result.get("wards_with_issues", {}).items():
                if isinstance(issues, list):
                    for issue in issues[:3]:
                        print(f"    - [{ward}] {issue}")
    
    total_files = len(results)
    valid_files = sum(1 for r in results.values() if r["valid"])
    
    summary = {
        "total_councils": total_files,
        "valid_councils": valid_files,
        "invalid_councils": total_files - valid_files,
        "details": results,
    }
    
    OUTPUT_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    
    print(f"\nSummary: {valid_files}/{total_files} councils valid")
    print(f"Report saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
