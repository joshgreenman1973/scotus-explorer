#!/usr/bin/env python3
"""Process SCDB datasets into compact JSON for the SCOTUS Explorer."""
import csv
import json
import sys
from collections import defaultdict

# SCDB Issue Area codes -> readable names
ISSUE_AREAS = {
    1: "Criminal Procedure",
    2: "Civil Rights",
    3: "First Amendment",
    4: "Due Process",
    5: "Privacy",
    6: "Attorneys",
    7: "Unions",
    8: "Economic Activity",
    9: "Judicial Power",
    10: "Federalism",
    11: "Interstate Relations",
    12: "Federal Taxation",
    13: "Miscellaneous",
    14: "Private Action",
}

# SCDB Justice name codes -> readable names
JUSTICE_NAMES = {}  # Will be populated from justiceName field

# Clean SCDB justice names to last names
JUSTICE_CLEAN = {
    "HLBlack": "Black", "SFReed": "Reed", "FFrankfurter": "Frankfurter",
    "WODouglas": "Douglas", "FMurphy": "Murphy", "RHJackson": "Jackson",
    "WBRutledge": "Rutledge", "HHBurton": "Burton", "FMVinson": "Vinson",
    "TCClark": "Clark", "SMinton": "Minton", "EWarren": "Warren",
    "JHarlan2": "Harlan", "WJBrennan": "Brennan", "CEWhittaker": "Whittaker",
    "PSStewart": "Stewart", "BRWhite": "White", "AJGoldberg": "Goldberg",
    "AFortas": "Fortas", "TMarshall": "Marshall", "WEBurger": "Burger",
    "HABlackmun": "Blackmun", "LFPowell": "Powell", "WHRehnquist": "Rehnquist",
    "JPStevens": "Stevens", "SDOConnor": "O'Connor", "AScalia": "Scalia",
    "AMKennedy": "Kennedy", "DHSouter": "Souter", "CThomas": "Thomas",
    "RBGinsburg": "Ginsburg", "SGBreyer": "Breyer", "JGRoberts": "Roberts",
    "SAAlito": "Alito", "SSotomayor": "Sotomayor", "EKagan": "Kagan",
    "NMGorsuch": "Gorsuch", "BMKavanaugh": "Kavanaugh", "ACBarrett": "Barrett",
    "KBJackson": "Jackson",
}

# SCDB vote codes
# 1=majority, 2=dissent, 3=regular concurrence, 4=special concurrence,
# 5=judgment of the Court, 6=dissent from denial of cert, 7=jurisdictional dissent, 8=not participating
VOTE_MAJORITY = {1, 3, 4, 5}  # These are "with majority" broadly
VOTE_DISSENT = {2}
VOTE_CONCURRENCE = {3, 4}

# Opinion codes: 1=wrote majority, 2=wrote concurrence, 3=wrote dissent, etc.

# Decision direction: 1=conservative, 2=liberal, 3=unspecifiable
DIRECTION_LABELS = {1: "conservative", 2: "liberal", 3: "unspecifiable"}

# Chief Justice eras
CHIEF_ERAS = {
    1: "Jay", 2: "Rutledge", 3: "Ellsworth", 4: "Marshall", 5: "Taney",
    6: "Chase", 7: "Waite", 8: "Fuller", 9: "White", 10: "Taft",
    11: "Hughes", 12: "Stone", 13: "Vinson", 14: "Warren", 15: "Burger",
    16: "Rehnquist", 17: "Roberts"
}

def safe_int(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return None

def parse_cases(case_file):
    """Parse case-centered CSV into dict keyed by caseId."""
    cases = {}
    with open(case_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_id = row['caseId']
            term = safe_int(row['term'])
            issue_area = safe_int(row['issueArea'])
            maj_votes = safe_int(row['majVotes'])
            min_votes = safe_int(row['minVotes'])
            direction = safe_int(row['decisionDirection'])

            cases[case_id] = {
                'id': case_id,
                'name': row['caseName'].strip('"'),
                'term': term,
                'date': row['dateDecision'],
                'cite': row['usCite'].strip('"'),
                'docket': row['docket'].strip('"'),
                'issueArea': issue_area,
                'issueAreaName': ISSUE_AREAS.get(issue_area, 'Other'),
                'issue': safe_int(row['issue']),
                'majVotes': maj_votes,
                'minVotes': min_votes,
                'vote': f"{maj_votes}-{min_votes}" if maj_votes and min_votes is not None else "",
                'direction': DIRECTION_LABELS.get(direction, ''),
                'chief': CHIEF_ERAS.get(safe_int(row['chief']), ''),
                'majWriter': safe_int(row['majOpinWriter']),
                'precedent': safe_int(row['precedentAlteration']),  # 1=altered, 0=not
                'unconstitutional': safe_int(row['declarationUncon']),
                'disposition': safe_int(row['caseDisposition']),
            }
    return cases

def parse_justice_votes(justice_file, cases):
    """Parse justice-centered CSV to add vote breakdowns to cases."""
    justice_data = defaultdict(list)

    with open(justice_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_id = row['caseId']
            if case_id not in cases:
                continue

            justice_id = safe_int(row['justice'])
            justice_name = row['justiceName'].strip('"')
            vote = safe_int(row['vote'])
            opinion = safe_int(row['opinion'])
            majority = safe_int(row['majority'])

            clean_name = JUSTICE_CLEAN.get(justice_name, justice_name)

            JUSTICE_NAMES[justice_id] = clean_name

            justice_data[case_id].append({
                'id': justice_id,
                'name': clean_name,
                'vote': vote,
                'opinion': opinion,
                'majority': majority,
            })

    return justice_data

def build_output(cases, justice_data):
    """Build compact JSON output."""
    output = []

    for case_id, case in sorted(cases.items(), key=lambda x: x[1]['term'] or 0):
        votes = justice_data.get(case_id, [])

        # Find opinion author
        author = None
        concurrences = []
        dissents = []
        majority_justices = []

        for v in votes:
            if v['vote'] == 8:  # not participating
                continue
            if v['opinion'] == 1 or (v['majority'] == 2 and case.get('majWriter') == v['id']):
                author = v['name']
            if v['vote'] in VOTE_CONCURRENCE:
                concurrences.append(v['name'])
            elif v['vote'] in VOTE_DISSENT:
                dissents.append(v['name'])
            if v['majority'] == 2:  # in majority
                majority_justices.append(v['name'])

        # If we didn't find author from opinion field, use majWriter
        if not author:
            writer_id = case.get('majWriter')
            if writer_id and writer_id in JUSTICE_NAMES:
                author = JUSTICE_NAMES[writer_id]

        entry = {
            'id': case['id'],
            'n': case['name'],  # compact keys
            't': case['term'],
            'd': case['date'],
            'c': case['cite'],
            'ia': case['issueArea'],
            'v': case['vote'],
            'dir': case['direction'],
            'ch': case['chief'],
            'a': author or '',
            'con': concurrences if concurrences else None,
            'dis': dissents if dissents else None,
            'maj': majority_justices if majority_justices else None,
            'pa': case['precedent'],  # precedent altered
            'uc': case['unconstitutional'],  # declared unconstitutional
        }
        # Remove None values for compactness
        entry = {k: v for k, v in entry.items() if v is not None}
        output.append(entry)

    return output

def main():
    case_file = 'SCDB_2025_01_caseCentered_Citation.csv'
    justice_file = 'SCDB_2025_01_justiceCentered_Citation.csv'

    print(f"Parsing cases...", file=sys.stderr)
    cases = parse_cases(case_file)
    print(f"  {len(cases)} cases loaded", file=sys.stderr)

    print(f"Parsing justice votes...", file=sys.stderr)
    justice_data = parse_justice_votes(justice_file, cases)
    print(f"  {len(justice_data)} cases with vote data", file=sys.stderr)

    print(f"Building output...", file=sys.stderr)
    output = build_output(cases, justice_data)

    # Also output issue area mapping
    result = {
        'issueAreas': ISSUE_AREAS,
        'cases': output,
        'meta': {
            'source': 'Supreme Court Database (SCDB) 2025 Release 01',
            'coverage': '1946-2024 terms',
            'totalCases': len(output),
        }
    }

    print(json.dumps(result, separators=(',', ':')))
    print(f"\nDone! {len(output)} cases output", file=sys.stderr)

if __name__ == '__main__':
    main()
