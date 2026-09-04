# -*- coding: utf-8 -*-
"""Targeted third pass using discovered clues."""
import requests, re, json

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
     "Accept": "application/json, text/plain, */*"}


def probe(name, method, url, body=None, extra_headers=None):
    try:
        h = dict(H)
        if extra_headers: h.update(extra_headers)
        if method == "POST":
            h["Content-Type"] = "application/json"
            r = requests.post(url, headers=h, json=body or {}, timeout=15)
        else:
            r = requests.get(url, headers=h, timeout=15)
        try:
            d = r.json()
        except Exception:
            d = None
        print(f"[{r.status_code}] {name}: {url[:80]}")
        if d and isinstance(d, dict):
            print(f"   keys={list(d.keys())[:8]}")
            # Try locate job list
            for k,v in d.items():
                if isinstance(v, list) and len(v) > 0:
                    print(f"   {k}: list[{len(v)}] first keys: {list(v[0].keys())[:8] if isinstance(v[0],dict) else '?'}")
                elif isinstance(v, dict):
                    for kk,vv in v.items():
                        if isinstance(vv, list) and len(vv) > 0:
                            print(f"   {k}.{kk}: list[{len(vv)}]")
                elif isinstance(v, int):
                    print(f"   {k}={v}")
        return r, d
    except Exception as e:
        print(f"[ERR] {name}: {e}")
        return None, None


# ============= JUSTEAT - Phenom standard endpoint =============
print("\n### JUSTEAT ###")
# Phenom uses POST /api/careers/searchJobs with body / or a widget-based fetch
probe("Justeat POST", "POST",
      "https://careers.justeattakeaway.com/api/careers/searchJobs",
      body={"pageName":"search","siteType":"external","tenantId":"takeglobal",
            "domain":"justeattakeaway.com","limit":20,"start":0,"jobsRefiners":{}})

probe("Justeat with tenant hdr", "GET",
      "https://careers.justeattakeaway.com/api/careers/searchJobs?limit=20",
      extra_headers={"x-tenant-id":"takeglobal","referer":"https://careers.justeattakeaway.com/global/en"})

# Try widget-based (Phenom classic)
probe("Justeat widget", "POST",
      "https://careers.justeattakeaway.com/widgets/jobsearch",
      body={"limit":20,"offset":0})

# Try known Phenom pattern
probe("Justeat search classic", "GET",
      "https://careers.justeattakeaway.com/services/search?q=&limit=20",
      extra_headers={"Referer":"https://careers.justeattakeaway.com/global/en"})


# ============= CISCO - Phenom =============
print("\n### CISCO ###")
probe("Cisco POST search", "POST",
      "https://jobs.cisco.com/api/careers/searchJobs",
      body={"pageName":"search","siteType":"external","tenantId":"ciscisglobal",
            "domain":"cisco.com","limit":20,"start":0,"jobsRefiners":{}})

probe("Cisco widget", "GET",
      "https://jobs.cisco.com/widgets/jobsearch?limit=20&domain=cisco.com")

# Try official Cisco jobs endpoint (they had one)
probe("Cisco search page json", "GET",
      "https://jobs.cisco.com/jobs/SearchJobs/?21178=%5B37704%5D&21178_format=6020&projectRecordsPerPage=25&format=json",
      extra_headers={"Accept":"application/json"})


# ============= BOOKING - JibeApply =============
print("\n### BOOKING ###")
# JibeApply uses /api or angular endpoints
probe("Booking joblist", "GET",
      "https://jobs.booking.com/booking/api/joblist?page=1&pageSize=20")

probe("Booking careers-api", "GET",
      "https://jobs.booking.com/booking/api/careers-search?limit=20")

probe("Booking joblist form", "POST",
      "https://jobs.booking.com/booking/joblist",
      body={"pageIndex":1,"pageSize":20},
      extra_headers={"Referer":"https://jobs.booking.com/booking/jobs"})

# Inspect Booking HTML for XHR/fetch URLs
print("--- Booking HTML dig ---")
r = requests.get("https://jobs.booking.com/booking/jobs", headers=H, timeout=15)
html = r.text
xhr_hits = set(re.findall(r'["\'](/booking/[a-zA-Z0-9\-_/]+(?:api|search|jobs|list)[a-zA-Z0-9\-_/?=&]*)["\']', html))
print(f"  potential API paths: {len(xhr_hits)}")
for p in list(xhr_hits)[:12]:
    print("   ", p)


# ============= ATLASSIAN - Workday with better body =============
print("\n### ATLASSIAN ###")
# Common Atlassian Workday endpoint variants (from public web)
for site in ["Careers","External","external","careers","Atlassian_Careers","External_Career_Site"]:
    for wd in ["wd3","wd5","wd1"]:
        url = f"https://atlassian.{wd}.myworkdayjobs.com/wday/cxs/atlassian/{site}/jobs"
        r, d = probe(f"Atl {wd}/{site}", "POST", url,
                     body={"limit":20,"offset":0,"searchText":"","appliedFacets":{}},
                     extra_headers={"Origin":f"https://atlassian.{wd}.myworkdayjobs.com",
                                    "Referer":f"https://atlassian.{wd}.myworkdayjobs.com/en-US/{site}"})
        if r and r.status_code == 200 and d:
            print("   FOUND!", url); 
            break
    else:
        continue
    break


# ============= REVOLUT Workable full jobs endpoint =============
print("\n### REVOLUT ###")
probe("Revolut Workable v3 jobs", "GET",
      "https://apply.workable.com/api/v3/accounts/revolut/jobs?state=published")

probe("Revolut Workable pub board", "POST",
      "https://apply.workable.com/api/v1/widget/accounts/revolut/jobs",
      body={"query":"","limit":20})

# Their actual URL - jobs listed on revolut.com/careers loads via lever probably
probe("Revolut jobs page fetch", "GET",
      "https://www.revolut.com/careers/positions/",
      extra_headers={"Accept":"text/html"})


# ============= BACKBASE - look for iframe / apply page =============
print("\n### BACKBASE ###")
# Check if backbase has jobs.lever.co iframe
r = requests.get("https://www.backbase.com/careers/jobs", headers=H, timeout=15)
html = r.text
# Look for iframe src
iframes = re.findall(r'<iframe[^>]+src="([^"]+)"', html)
print(f"  iframes: {iframes}")
# apply URLs
apply = re.findall(r'https?://[^\s"\'<>]*(?:apply|jobs|careers)[^\s"\'<>]{5,80}', html)
uniq = sorted(set(apply))
print(f"  apply URLs found: {len(uniq)}")
for a in uniq[:20]:
    print("   ", a)
