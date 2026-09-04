# -*- coding: utf-8 -*-
"""
Re-score all jobs currently in DB with the new criteria (Strategy & Ops added).
Show new HIGH/MED matches that would emerge.
"""
import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DB_PATH, SCORE_THRESHOLD_HIGH, SCORE_THRESHOLD_MEDIUM
from matcher import score_job

# But: DB doesn't store descriptions. So we can only re-score title+location.
# Fetch fresh data for full re-score - this uses the real fetcher chain.
from unified_scraper import scan_all_companies

print("Rescanning all 25 companies with NEW criteria (Strategy & Ops added)...")
print("(this simulates what the next automatic scan will do)\n")

results = scan_all_companies()

new_high = []
new_med = []
low_but_close = []  # 40-49 near-miss for visibility

for company, jobs, err in results:
    if err:
        continue
    for j in jobs:
        title = j.get("title","")
        loc = j.get("location","")
        desc = j.get("description","")
        url = j.get("url","")
        r = score_job(title, loc, desc)
        if not r["passes_hard_filters"]:
            continue
        s = r["score"]
        item = (company, title, loc, s, url)
        if s >= SCORE_THRESHOLD_HIGH:
            new_high.append(item)
        elif s >= SCORE_THRESHOLD_MEDIUM:
            new_med.append(item)
        elif s >= 40:
            low_but_close.append(item)

# Show
print(f"\n{'='*80}\nHIGH matches (score >= 70): {len(new_high)}\n{'='*80}")
for c, t, l, s, u in sorted(new_high, key=lambda x: -x[3])[:30]:
    print(f"  [{s}] {c:<12} {t[:65]}")
    print(f"       {l[:80]}")

print(f"\n{'='*80}\nMEDIUM matches (50-69): {len(new_med)}\n{'='*80}")
for c, t, l, s, u in sorted(new_med, key=lambda x: -x[3])[:30]:
    print(f"  [{s}] {c:<12} {t[:65]}  ({l[:40]})")

print(f"\nGrand total: {len(new_high)} HIGH + {len(new_med)} MEDIUM = {len(new_high)+len(new_med)} matches")
