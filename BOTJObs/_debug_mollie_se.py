# -*- coding: utf-8 -*-
"""Debug: why Mollie Sales Engineer I scored 57 instead of 70+?"""
import sys, os, requests, html, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from matcher import score_job

# Fetch fresh data from Mollie Ashby
url = "https://api.ashbyhq.com/posting-api/job-board/mollie?includeCompensation=false"
r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
data = r.json()

target = None
for j in data.get("jobs", []):
    if "sales engineer" in j.get("title","").lower():
        target = j; break

if not target:
    print("Not found")
    sys.exit(1)

title = target.get("title","")
loc   = target.get("locationName","") or target.get("location","")
desc  = target.get("descriptionHtml") or target.get("description","") or ""
# strip html
desc_clean = re.sub(r"<[^>]+>", " ", html.unescape(desc))
desc_clean = re.sub(r"\s+", " ", desc_clean).strip()

print("=" * 70)
print(f"TITLE:    {title!r}")
print(f"LOCATION: {loc!r}")
print(f"URL:      {target.get('jobUrl','')}")
print(f"DESC size: {len(desc_clean)} chars")
print("=" * 70)

result = score_job(title, loc, desc_clean)
print(f"\nSCORE:    {result['score']}/100")
print(f"passes:   {result['passes_hard_filters']}")
if result.get("excluded_by"):
    print(f"EXCLUDED: {result['excluded_by']}")
print(f"\nBREAKDOWN:")
for k, v in result["breakdown"].items():
    print(f"  {k:<10} = {v}")

print(f"\nMATCHED KEYWORDS:")
for cat, kws in result["matched"].items():
    if kws:
        print(f"  {cat:<10}: {kws}")
    else:
        print(f"  {cat:<10}: (nothing)")

print("\n" + "=" * 70)
print("DESC first 800 chars:")
print(desc_clean[:800])
print("...")
print("DESC last 800 chars:")
print(desc_clean[-800:])
