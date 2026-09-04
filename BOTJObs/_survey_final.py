# -*- coding: utf-8 -*-
"""
Final pass - target the 8 remaining companies with platform-specific API calls.
Workday CXS (POST), Phenom (search endpoint), iCIMS, custom Backbase, etc.
"""
import requests, json

HEADERS_JSON = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "Origin": "",  # per host
    "Referer": "",
}

results = {}

def rec(company, ok, endpoint, count, notes=""):
    results[company] = {"ok": ok, "endpoint": endpoint,
                        "count": count, "notes": notes}
    tag = "OK " if ok else "-- "
    print(f"{tag}{company:<12} count={count:<8} {endpoint[:75]}   {notes}")

# =============================================================
# 1. REVOLUT - probably Greenhouse under different slug (try alternates)
# =============================================================
print("\n--- REVOLUT ---")
for slug in ["revolut", "revolutgroup", "revoluttechnologies", "revolutlimited"]:
    try:
        r = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
                         headers=HEADERS_JSON, timeout=10)
        if r.status_code == 200:
            n = len(r.json().get("jobs", []))
            if n > 0:
                rec("Revolut", True, f"greenhouse:{slug}", n)
                break
    except Exception: pass
else:
    # Try Lever, Ashby, SmartRecruiters
    for tester in [
        ("lever", "https://api.lever.co/v0/postings/revolut?mode=json"),
        ("smart", "https://api.smartrecruiters.com/v1/companies/Revolut/postings?limit=1"),
        ("ashby", "https://api.ashbyhq.com/posting-api/job-board/revolut"),
    ]:
        try:
            r = requests.get(tester[1], headers=HEADERS_JSON, timeout=10)
            if r.status_code == 200:
                d = r.json()
                cnt = (len(d) if isinstance(d, list) else
                       d.get("totalFound") or len(d.get("jobs", [])))
                if cnt and cnt > 0:
                    rec("Revolut", True, tester[1], cnt); break
        except Exception: pass
    else:
        rec("Revolut", False, "unknown", 0, "needs deep probe")

# =============================================================
# 2. BACKBASE - try Recruitee / Personio / Greenhouse
# =============================================================
print("\n--- BACKBASE ---")
tests = [
    ("Recruitee", "https://backbase.recruitee.com/api/offers/"),
    ("Personio",  "https://backbase.jobs.personio.com/xml"),
    ("Greenhouse","https://boards-api.greenhouse.io/v1/boards/backbase/jobs"),
    ("Lever",     "https://api.lever.co/v0/postings/backbase?mode=json"),
    ("SmartR",    "https://api.smartrecruiters.com/v1/companies/Backbase/postings?limit=1"),
    ("Ashby",     "https://api.ashbyhq.com/posting-api/job-board/backbase"),
]
for name, url in tests:
    try:
        r = requests.get(url, headers=HEADERS_JSON, timeout=10)
        if r.status_code == 200:
            if name == "Personio" and b"<position>" in r.content:
                cnt = r.text.count("<position>")
                rec("Backbase", True, url, cnt, name); break
            elif name != "Personio":
                d = r.json()
                cnt = (len(d) if isinstance(d, list) else
                       d.get("totalFound") or len(d.get("jobs", [])) or
                       len(d.get("offers", [])))
                if cnt and cnt > 0:
                    rec("Backbase", True, url, cnt, name); break
    except Exception: pass
else:
    rec("Backbase", False, "unknown", 0, "needs deep probe")

# =============================================================
# 3. ATLASSIAN - Workday tenant
# =============================================================
print("\n--- ATLASSIAN ---")
# Workday format: POST to /wday/cxs/{tenant}/{site}/jobs with body {}
wd_urls = [
    "https://atlassian.wd3.myworkdayjobs.com/wday/cxs/atlassian/External/jobs",
    "https://atlassian.wd5.myworkdayjobs.com/wday/cxs/atlassian/External/jobs",
]
found = False
for url in wd_urls:
    try:
        h = dict(HEADERS_JSON); h["Origin"] = "https://atlassian.wd3.myworkdayjobs.com"
        r = requests.post(url, json={"appliedFacets": {}, "limit": 20, "offset": 0,
                                     "searchText": ""},
                          headers=h, timeout=15)
        if r.status_code == 200:
            d = r.json()
            cnt = d.get("total") or len(d.get("jobPostings", []))
            if cnt and cnt > 0:
                rec("Atlassian", True, url, cnt, "Workday POST"); found = True; break
    except Exception: pass
if not found:
    rec("Atlassian", False, "unknown", 0)

# =============================================================
# 4. OPTIVER - custom or Greenhouse
# =============================================================
print("\n--- OPTIVER ---")
tests = [
    ("greenhouse", "https://boards-api.greenhouse.io/v1/boards/optiver/jobs"),
    ("recruitee",  "https://optiver.recruitee.com/api/offers/"),
    ("wp",         "https://www.optiver.com/wp-json/wp/v2/pages?slug=jobs&per_page=1"),
    ("wp-jobs",    "https://www.optiver.com/wp-json/wp/v2/careers?per_page=100"),
    ("wp-vacancy", "https://www.optiver.com/wp-json/wp/v2/vacancy?per_page=100"),
    ("wp-search",  "https://www.optiver.com/wp-json/wp/v2/search?search=engineer&per_page=100&subtype=vacancy"),
]
for name, url in tests:
    try:
        r = requests.get(url, headers=HEADERS_JSON, timeout=10)
        if r.status_code == 200:
            d = r.json()
            cnt = (len(d) if isinstance(d, list) else
                   d.get("totalFound") or len(d.get("jobs", [])) or
                   len(d.get("offers", [])))
            if cnt and cnt > 0:
                rec("Optiver", True, url, cnt, name); break
    except Exception: pass
else:
    rec("Optiver", False, "unknown", 0)

# =============================================================
# 5. JUSTEAT - Phenom search API
# =============================================================
print("\n--- JUSTEAT ---")
tests = [
    "https://careers.justeattakeaway.com/api/apply/v2/jobs?domain=justeattakeaway.com&start=0&num=10",
    "https://careers.justeattakeaway.com/api/careers/search?limit=20",
    "https://justeattakeaway.phenompeople.com/api/careers/search?limit=20",
    "https://careers.justeattakeaway.com/api/careers/searchJobs?limit=20",
]
for url in tests:
    try:
        r = requests.get(url, headers=HEADERS_JSON, timeout=10)
        if r.status_code == 200:
            try:
                d = r.json()
                cnt = (d.get("totalCount") or d.get("total") or
                       len(d.get("jobs", [])) or len(d.get("data", [])))
                if cnt and cnt > 0:
                    rec("Justeat", True, url, cnt); break
            except Exception: pass
    except Exception: pass
else:
    rec("Justeat", False, "unknown", 0)

# =============================================================
# 6. BOOKING - iCIMS
# =============================================================
print("\n--- BOOKING ---")
tests = [
    "https://booking.icims.com/jobs/search?ss=1&hashed=-1&mobile=false&width=1004&height=500&bga=true&needsRedirect=false",
    "https://careers.booking.com/api/jobs?limit=20",
    "https://careers.booking.com/api/careers/search?limit=20",
    "https://careers.booking.com/api/positions",
    "https://careers.booking.com/en/api/positions",
]
h_bk = {**HEADERS_JSON, "Origin": "https://careers.booking.com",
        "Referer": "https://careers.booking.com/"}
for url in tests:
    try:
        r = requests.get(url, headers=h_bk, timeout=10)
        if r.status_code == 200:
            try:
                d = r.json()
                cnt = (d.get("totalCount") or d.get("total") or
                       len(d.get("jobs", [])) or len(d.get("positions", [])) or
                       len(d.get("data", [])))
                if cnt and cnt > 0:
                    rec("Booking", True, url, cnt); break
            except Exception: pass
    except Exception: pass
else:
    rec("Booking", False, "unknown", 0)

# =============================================================
# 7. WORKDAY (the company) - Workday tenant
# =============================================================
print("\n--- WORKDAY (company) ---")
wd_urls = [
    "https://workday.wd5.myworkdayjobs.com/wday/cxs/workday/Workday/jobs",
    "https://workday.wd12.myworkdayjobs.com/wday/cxs/workday/Workday/jobs",
    "https://workday.wd1.myworkdayjobs.com/wday/cxs/workday/Workday/jobs",
    "https://workday.wd5.myworkdayjobs.com/wday/cxs/workday/External/jobs",
]
for url in wd_urls:
    try:
        r = requests.post(url,
                          json={"appliedFacets": {}, "limit": 20,
                                "offset": 0, "searchText": ""},
                          headers=HEADERS_JSON, timeout=15)
        if r.status_code == 200:
            d = r.json()
            cnt = d.get("total") or len(d.get("jobPostings", []))
            if cnt and cnt > 0:
                rec("Workday", True, url, cnt, "Workday POST"); break
    except Exception: pass
else:
    rec("Workday", False, "unknown", 0)

# =============================================================
# 8. CISCO - Phenom search
# =============================================================
print("\n--- CISCO ---")
tests = [
    "https://jobs.cisco.com/api/apply/v2/jobs?domain=cisco.com&start=0&num=10",
    "https://jobs.cisco.com/api/careers/search?limit=20",
    "https://cisco.phenompeople.com/api/careers/search?limit=20",
    "https://jobs.cisco.com/api/apply/v2/jobs?domain=cisco.com",
]
for url in tests:
    try:
        r = requests.get(url, headers=HEADERS_JSON, timeout=10)
        if r.status_code == 200:
            try:
                d = r.json()
                cnt = (d.get("totalCount") or d.get("total") or
                       d.get("filters", {}).get("totalHits") or
                       len(d.get("jobs", [])) or len(d.get("data", [])))
                if cnt and cnt > 0:
                    rec("Cisco", True, url, cnt); break
            except Exception: pass
    except Exception: pass
else:
    rec("Cisco", False, "unknown", 0)

# =============================================================
print("\n" + "="*80)
ok = sum(1 for v in results.values() if v["ok"])
print(f"RESULT: {ok}/{len(results)} solved")

with open("_survey_final.json","w") as f:
    json.dump(results, f, indent=2)
