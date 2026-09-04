# -*- coding: utf-8 -*-
"""
Final pass v2 - use hints found from HTML inspection.
- Justeat, Cisco: Phenom (confirmed by phenompeople.com CDNs)
- Booking: iCIMS at jobs.booking.com/booking/jobs
- Atlassian, Optiver, Backbase: try more Workday tenants and API variants
- Revolut: 403 Cloudflare - try LinkedIn or scraped HTML
"""
import requests, re, json

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
     "Accept": "application/json, text/plain, */*",
     "Accept-Language": "en-US,en;q=0.9"}


def test_json(name, url, method="GET", body=None, headers=None, count_keys=("totalCount","total","hits","count")):
    """Test an endpoint and try to extract job count."""
    try:
        h = dict(H); 
        if headers: h.update(headers)
        if method == "POST":
            r = requests.post(url, headers={**h, "Content-Type":"application/json"},
                              json=body or {}, timeout=15)
        else:
            r = requests.get(url, headers=h, timeout=15)
        if r.status_code != 200:
            return None, f"HTTP{r.status_code}"
        try:
            d = r.json()
        except Exception:
            return None, "not-json"
        # Try many locations
        cnt = None
        for k in count_keys:
            if isinstance(d, dict) and k in d:
                v = d[k]
                if isinstance(v, int): cnt = v; break
                if isinstance(v, list): cnt = len(v); break
                if isinstance(v, dict):
                    for kk in count_keys + ("value","totalHits"):
                        if kk in v and isinstance(v[kk], int):
                            cnt = v[kk]; break
                    if cnt is not None: break
        if cnt is None and isinstance(d, dict):
            # look for common list keys
            for lk in ("jobs","jobPostings","postings","results","data","items","offers","refineSearch"):
                v = d.get(lk)
                if isinstance(v, list): cnt = len(v); break
                if isinstance(v, dict) and "jobs" in v:
                    cnt = len(v["jobs"]) if isinstance(v["jobs"], list) else None
                    if cnt is not None: break
        if cnt is None and isinstance(d, list):
            cnt = len(d)
        return cnt, "ok"
    except Exception as e:
        return None, f"ERR:{type(e).__name__}"


# =================================
# 1. JUSTEAT - Phenom search
# =================================
print("--- JUSTEAT ---")
justeat_tries = [
    ("https://careers.justeattakeaway.com/api/careers/searchJobs?limit=20", "GET", None),
    ("https://careers.justeattakeaway.com/api/careers/searchJobs", "POST", {"limit":20,"start":0}),
    ("https://careers.justeattakeaway.com/api/apply/v2/jobs?domain=justeattakeaway.com&num=10&start=0", "GET", None),
    ("https://careers.justeattakeaway.com/widgets", "GET", None),
    ("https://careers.justeattakeaway.com/api/careers/search?limit=20", "GET", None),
    ("https://content-ir.phenompeople.com/api/content-delivery/caasContentV1?ClientId=takeglobal", "GET", None),
    ("https://careers.justeattakeaway.com/api/careers/searchJobs?tags=&limit=100", "GET", None),
]
for url, method, body in justeat_tries:
    cnt, note = test_json("Justeat", url, method, body)
    if cnt and cnt > 0:
        print(f"  OK  count={cnt}  {url[:90]}")
        break
    print(f"  --  {note:<15} {url[:90]}")

# =================================
# 2. CISCO - Phenom
# =================================
print("\n--- CISCO ---")
cisco_tries = [
    ("https://jobs.cisco.com/api/careers/searchJobs?limit=20", "GET", None),
    ("https://jobs.cisco.com/api/careers/searchJobs", "POST", {"limit":20,"start":0}),
    ("https://jobs.cisco.com/api/apply/v2/jobs?domain=cisco.com&num=10&start=0", "GET", None),
    ("https://jobs.cisco.com/api/careers/search?limit=20", "GET", None),
    ("https://cisco.jobs/en/api/careers/searchJobs?limit=20", "GET", None),
    ("https://cisco.contentsv.phenompeople.com/api/careers/searchJobs", "POST", {"limit":20}),
]
for url, method, body in cisco_tries:
    cnt, note = test_json("Cisco", url, method, body)
    if cnt and cnt > 0:
        print(f"  OK  count={cnt}  {url[:90]}")
        break
    print(f"  --  {note:<15} {url[:90]}")

# =================================
# 3. BOOKING - iCIMS
# =================================
print("\n--- BOOKING ---")
booking_tries = [
    ("https://jobs.booking.com/booking/jobs?in_iframe=1&mobile=false&width=1004&height=500", "GET", None),
    ("https://jobs.booking.com/api-jobs?searchTerm=&categoryOption=&locationOption=&pageIndex=1", "GET", None),
    ("https://jobs.booking.com/booking/api-jobs?searchTerm=", "GET", None),
    ("https://booking.icims.com/api/careers/jobs?limit=20", "GET", None),
    ("https://careers.booking.com/api/jobs?limit=20&_t=1", "GET", None),
    ("https://careers.booking.com/graphql", "POST",
     {"query": "{jobs(limit:5){id title location}}"}),
    ("https://jobs.booking.com/booking/api-jobs", "GET", None),
]
for url, method, body in booking_tries:
    cnt, note = test_json("Booking", url, method, body)
    if cnt and cnt > 0:
        print(f"  OK  count={cnt}  {url[:90]}")
        break
    print(f"  --  {note:<15} {url[:90]}")

# =================================
# 4. ATLASSIAN - try more Workday tenants
# =================================
print("\n--- ATLASSIAN ---")
atlassian_urls = [
    "https://atlassian.wd5.myworkdayjobs.com/wday/cxs/atlassian/Careers/jobs",
    "https://atlassian.wd3.myworkdayjobs.com/wday/cxs/atlassian/careers/jobs",
    "https://myatlassiancareers.wd3.myworkdayjobs.com/wday/cxs/myatlassiancareers/Careers/jobs",
    "https://atlassian.wd12.myworkdayjobs.com/wday/cxs/atlassian/Careers/jobs",
    "https://wd5.myworkdayjobs.com/wday/cxs/atlassian/Careers/jobs",
]
for url in atlassian_urls:
    cnt, note = test_json("Atl", url, "POST", 
                          {"appliedFacets":{},"limit":20,"offset":0,"searchText":""})
    if cnt and cnt > 0:
        print(f"  OK  count={cnt}  {url[:90]}")
        break
    print(f"  --  {note:<15} {url[:90]}")

# =================================
# 5. OPTIVER - custom / wp
# =================================
print("\n--- OPTIVER ---")
optiver_tries = [
    ("https://www.optiver.com/wp-json/wp/v2/pages?slug=jobs&per_page=1", "GET", None),
    ("https://www.optiver.com/wp-json/optiver/v1/jobs", "GET", None),
    ("https://www.optiver.com/wp-json/optiver/v1/careers", "GET", None),
    ("https://www.optiver.com/wp-json/wp/v2/positions", "GET", None),
    ("https://www.optiver.com/wp-json/wp/v2/opening", "GET", None),
    ("https://www.optiver.com/wp-json/wp/v2/job", "GET", None),
    ("https://boards-api.greenhouse.io/v1/boards/optiverus/jobs", "GET", None),
    ("https://boards-api.greenhouse.io/v1/boards/optivereurope/jobs", "GET", None),
]
for url, method, body in optiver_tries:
    cnt, note = test_json("Optiver", url, method, body)
    if cnt and cnt > 0:
        print(f"  OK  count={cnt}  {url[:90]}")
        break
    print(f"  --  {note:<15} {url[:90]}")

# =================================
# 6. BACKBASE - inspect HTML more carefully
# =================================
print("\n--- BACKBASE (deep HTML dig) ---")
try:
    r = requests.get("https://www.backbase.com/careers/jobs", headers=H, timeout=15)
    html = r.text
    # look for JSON script tags
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    print(f"  total scripts: {len(scripts)}")
    for i, s in enumerate(scripts):
        if 'engineer' in s.lower() or 'position' in s.lower() or 'vacancy' in s.lower() or 'greenhouse' in s.lower() or 'workday' in s.lower():
            # first 400 chars
            snippet = s[:400].replace('\n',' ')
            print(f"  script[{i}] hint: {snippet[:250]}")
    # search html for known ATS domains
    for kw in ('workable','greenhouse','lever','ashby','recruitee','personio','teamtailor','workday','icims'):
        if kw in html.lower():
            print(f"  found kw: {kw}")
except Exception as e:
    print("  ERR:", e)

# =================================
# 7. REVOLUT - try LinkedIn public jobs page + wappalyzer clues
# =================================
print("\n--- REVOLUT ---")
rev_tries = [
    ("https://boards-api.greenhouse.io/v1/boards/revolutpeople/jobs", "GET", None),
    ("https://api.smartrecruiters.com/v1/companies/Revolut/postings?limit=1", "GET", None),
    ("https://api.smartrecruiters.com/v1/companies/RevolutLtd/postings?limit=1", "GET", None),
    ("https://revolut.jobs.personio.com/xml", "GET", None),
    ("https://apply.workable.com/api/v1/widget/accounts/revolut?details=true", "GET", None),
]
for url, method, body in rev_tries:
    cnt, note = test_json("Revolut", url, method, body)
    if cnt and cnt > 0:
        print(f"  OK  count={cnt}  {url[:90]}")
        break
    print(f"  --  {note:<15} {url[:90]}")
