# -*- coding: utf-8 -*-
"""Verifica quanti job Adyen ci sono ad Amsterdam."""
import requests
from collections import Counter

r = requests.get("https://boards-api.greenhouse.io/v1/boards/adyen/jobs",
                 headers={"User-Agent":"Mozilla/5.0"}, timeout=20)
data = r.json()
jobs = data.get("jobs", [])

total = len(jobs)
ams = [j for j in jobs if "amsterdam" in (j.get("location") or {}).get("name","").lower()]
mad = [j for j in jobs if "madrid" in (j.get("location") or {}).get("name","").lower()]

print(f"Adyen TOTAL open jobs (worldwide): {total}")
print(f"  - Amsterdam: {len(ams)}")
print(f"  - Madrid:    {len(mad)}")

print(f"\n--- All {len(ams)} Amsterdam jobs at Adyen ---")
for j in ams:
    print(f"  - {j['title']}  ({j['location']['name']})")

print(f"\n--- Top locations across all Adyen jobs ---")
loc_counter = Counter((j.get("location") or {}).get("name","?") for j in jobs)
for loc, cnt in loc_counter.most_common(10):
    print(f"  {cnt:>4}  {loc}")
