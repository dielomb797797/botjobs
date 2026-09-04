# -*- coding: utf-8 -*-
"""Deep-dive: perche' 69 vs 71? Verifico multi-location e offices field."""
import requests
from collections import Counter

# Standard endpoint
r1 = requests.get("https://boards-api.greenhouse.io/v1/boards/adyen/jobs",
                  headers={"User-Agent":"Mozilla/5.0"}, timeout=20)
d1 = r1.json()

# With content=true (returns full descriptions and offices)
r2 = requests.get("https://boards-api.greenhouse.io/v1/boards/adyen/jobs?content=true",
                  headers={"User-Agent":"Mozilla/5.0"}, timeout=30)
d2 = r2.json()

print(f"jobs endpoint (basic):        {len(d1.get('jobs', []))}")
print(f"jobs endpoint (content=true): {len(d2.get('jobs', []))}")

# Count Amsterdam matches with different criteria
jobs = d2.get("jobs", [])

# CRITERIA A: only location.name contains "amsterdam"
a = [j for j in jobs if "amsterdam" in (j.get("location") or {}).get("name","").lower()]

# CRITERIA B: also check "offices" (multi-office jobs)
def has_amsterdam(j):
    loc = ((j.get("location") or {}).get("name","") or "").lower()
    if "amsterdam" in loc: return True
    for off in j.get("offices", []) or []:
        if "amsterdam" in (off.get("name","") or "").lower():
            return True
    for off in j.get("departments", []) or []:  # unlikely but check
        pass
    return False

b = [j for j in jobs if has_amsterdam(j)]

print(f"\nCritera A (location contains Amsterdam):     {len(a)}")
print(f"Critera B (location OR offices Amsterdam):   {len(b)}")

# What's in offices for a few sample jobs?
print("\n--- Sample offices fields ---")
for j in jobs[:5]:
    print(f"{j['title'][:50]:50} | loc: {j.get('location',{}).get('name','?'):30} | offices: {[o.get('name') for o in j.get('offices',[]) or []]}")

# Check department endpoint if present
print("\n--- Try departments endpoint ---")
try:
    rd = requests.get("https://boards-api.greenhouse.io/v1/boards/adyen/departments",
                      headers={"User-Agent":"Mozilla/5.0"}, timeout=15).json()
    total_dept_jobs = sum(len(d.get("jobs",[])) for d in rd.get("departments",[]))
    print(f"Total jobs across all departments: {total_dept_jobs}")
except Exception as e:
    print(f"err: {e}")

# Check offices endpoint - sometimes Greenhouse has per-office job count
print("\n--- Try offices endpoint ---")
try:
    ro = requests.get("https://boards-api.greenhouse.io/v1/boards/adyen/offices",
                      headers={"User-Agent":"Mozilla/5.0"}, timeout=15).json()
    for o in ro.get("offices", []):
        name = o.get("name","?")
        # Some formats have child_ids and jobs count via cascade
        if "amsterdam" in name.lower() or "netherlands" in name.lower():
            print(f"  Office '{name}': {o}")
except Exception as e:
    print(f"err: {e}")

# What jobs have loc that CONTAINS multiple cities (semicolon or comma)?
print("\n--- Multi-location Amsterdam+other jobs (already counted) ---")
multi = [j for j in a if (";" in j.get("location",{}).get("name","") or 
                          "," in j.get("location",{}).get("name","") or
                          "/" in j.get("location",{}).get("name",""))]
for j in multi[:5]:
    print(f"  {j['title']}: {j['location']['name']}")

# Show jobs NOT counted where offices has Amsterdam
extra = [j for j in b if j not in a]
print(f"\n--- Jobs where offices=Amsterdam but location field says otherwise ({len(extra)}) ---")
for j in extra[:20]:
    print(f"  {j['title']}: loc={j.get('location',{}).get('name','?')} | offices={[o.get('name') for o in j.get('offices',[])]}")
