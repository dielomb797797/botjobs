# -*- coding: utf-8 -*-
"""
Debug specific endpoints - print raw JSON structure to find where jobs live.
"""
import requests, json

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
     "Accept": "application/json, text/plain, */*"}


def probe(name, method, url, body=None, extra_headers=None):
    print(f"\n{'='*70}\n{name}: {method} {url}\n{'='*70}")
    try:
        h = dict(H)
        if extra_headers: h.update(extra_headers)
        if method == "POST":
            h["Content-Type"] = "application/json"
            r = requests.post(url, headers=h, json=body or {}, timeout=15)
        else:
            r = requests.get(url, headers=h, timeout=15)
        print(f"HTTP {r.status_code} | size {len(r.content)} bytes")
        ct = r.headers.get("content-type","")
        print(f"Content-Type: {ct}")
        if r.status_code != 200:
            print("BODY (first 400):", r.text[:400])
            return
        # Try parse JSON
        try:
            d = r.json()
        except Exception:
            print("Not JSON. Raw first 500 chars:")
            print(r.text[:500])
            return
        # Print top-level structure
        if isinstance(d, dict):
            print("Top keys:", list(d.keys())[:15])
            for k, v in list(d.items())[:8]:
                if isinstance(v, list):
                    print(f"  {k!r}: list[{len(v)}]")
                    if v and isinstance(v[0], dict):
                        print(f"      first item keys: {list(v[0].keys())[:10]}")
                elif isinstance(v, dict):
                    print(f"  {k!r}: dict keys: {list(v.keys())[:8]}")
                    for kk, vv in list(v.items())[:5]:
                        if isinstance(vv, list):
                            print(f"      {kk!r}: list[{len(vv)}]")
                            if vv and isinstance(vv[0], dict):
                                print(f"          first item keys: {list(vv[0].keys())[:10]}")
                        elif isinstance(vv, (int,str,bool)):
                            print(f"      {kk!r}: {vv}")
                else:
                    val = str(v)[:80]
                    print(f"  {k!r}: {val}")
        elif isinstance(d, list):
            print(f"List of {len(d)} items")
            if d and isinstance(d[0], dict):
                print("  first item keys:", list(d[0].keys())[:10])
    except Exception as e:
        print("ERR:", e)


# ---------- JUSTEAT ----------
probe("Justeat search", "GET",
      "https://careers.justeattakeaway.com/api/careers/searchJobs?limit=20")

probe("Justeat apply v2", "GET",
      "https://careers.justeattakeaway.com/api/apply/v2/jobs?domain=justeattakeaway.com&num=10&start=0")

# ---------- CISCO ----------
probe("Cisco search", "GET",
      "https://jobs.cisco.com/api/careers/searchJobs?limit=20")

# ---------- BOOKING - try more paths ----------
probe("Booking direct html", "GET",
      "https://jobs.booking.com/booking/jobs")

# ---------- ATLASSIAN - Workday with proper body ----------
probe("Atlassian wd3", "POST",
      "https://atlassian.wd3.myworkdayjobs.com/wday/cxs/atlassian/careers/jobs",
      body={"appliedFacets":{},"limit":20,"offset":0,"searchText":""},
      extra_headers={"Origin":"https://atlassian.wd3.myworkdayjobs.com"})

# ---------- REVOLUT ----------
probe("Revolut SmartRecruiters", "GET",
      "https://api.smartrecruiters.com/v1/companies/Revolut/postings?limit=5")

probe("Revolut Workable", "GET",
      "https://apply.workable.com/api/v1/widget/accounts/revolut?details=true")

# ---------- BACKBASE - hunt HTML for JSON --------
print("\n" + "="*70 + "\nBACKBASE: fetch HTML and look for hidden JSON\n" + "="*70)
r = requests.get("https://www.backbase.com/careers/jobs", headers=H, timeout=15)
html = r.text
print(f"HTTP {r.status_code}, size {len(html)}")
# Find any JSON-looking blocks
import re
# script tags with type=application/json
json_scripts = re.findall(r'<script[^>]*type="application/(?:ld\+)?json"[^>]*>(.*?)</script>',
                          html, re.DOTALL)
print(f"application/json scripts: {len(json_scripts)}")
for i, s in enumerate(json_scripts[:3]):
    print(f"--- script[{i}] first 300 chars ---")
    print(s[:300])
# Also search for any 'workable'/'greenhouse'/'ashby'/'lever'/'personio' domain
for kw in ['workable','greenhouse','ashby','lever','personio','recruitee','teamtailor','iframe']:
    matches = re.findall(rf'https?://[^\s"\'<>]*{kw}[^\s"\'<>]*', html, re.IGNORECASE)
    if matches:
        print(f"  {kw}: {list(set(matches))[:3]}")
