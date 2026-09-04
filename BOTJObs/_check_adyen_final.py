# -*- coding: utf-8 -*-
"""Fonte di verita': endpoint /offices restituisce esattamente cio' che il sito mostra."""
import requests
from collections import defaultdict

H = {"User-Agent":"Mozilla/5.0"}
r = requests.get("https://boards-api.greenhouse.io/v1/boards/adyen/offices",
                 headers=H, timeout=20).json()

# Find Amsterdam office
ams_office = None
for o in r.get("offices", []):
    if o.get("name","").lower() == "amsterdam":
        ams_office = o
        break

if not ams_office:
    print("Amsterdam office NOT found"); exit()

# Collect all jobs (may appear in multiple departments; dedupe by id)
all_jobs = {}
for dept in ams_office.get("departments", []):
    for j in dept.get("jobs", []):
        jid = j.get("id")
        if jid and jid not in all_jobs:
            all_jobs[jid] = j

# Now also dedupe by internal_job_id (same posting cross-location)
by_internal = defaultdict(list)
for j in all_jobs.values():
    ij = j.get("internal_job_id")
    by_internal[ij].append(j)

unique_postings = len(by_internal)
total_job_ids   = len(all_jobs)

print(f"Adyen Amsterdam office:")
print(f"  Total job IDs shown:     {total_job_ids}")
print(f"  Unique postings:         {unique_postings} (dedupe by internal_job_id)")
print(f"  Departments in Amsterdam: {len(ams_office.get('departments',[]))}")

# What differs?
if total_job_ids != unique_postings:
    print(f"\n--- Duplicate internal_job_ids ({total_job_ids - unique_postings} extra) ---")
    for ij, group in by_internal.items():
        if len(group) > 1:
            for g in group:
                loc = (g.get("location") or {}).get("name","?")
                print(f"  internal_id={ij} | id={g.get('id')} | {g.get('title')} | loc={loc}")

# Also: check if a filter on the actual careers page uses a different logic.
# Adyen's site: https://careers.adyen.com/vacancies?locations=Amsterdam
# Let me also count via the standard /jobs endpoint with the offices field logic
r2 = requests.get("https://boards-api.greenhouse.io/v1/boards/adyen/jobs?content=true",
                  headers=H, timeout=30).json()
jobs = r2.get("jobs", [])

def has_amsterdam(j):
    loc = ((j.get("location") or {}).get("name","") or "").lower()
    if "amsterdam" in loc: return True
    for off in j.get("offices", []) or []:
        if "amsterdam" in (off.get("name","") or "").lower():
            return True
    return False

matches = [j for j in jobs if has_amsterdam(j)]
by_internal2 = defaultdict(list)
for j in matches:
    by_internal2[j.get("internal_job_id")].append(j)

print(f"\nCross-check via /jobs endpoint:")
print(f"  All jobs where Amsterdam is primary OR office: {len(matches)}")
print(f"  Unique by internal_job_id:                      {len(by_internal2)}")
