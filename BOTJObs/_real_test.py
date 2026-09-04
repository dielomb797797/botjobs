# -*- coding: utf-8 -*-
"""
REAL TEST: fetch actual jobs from 20 working APIs, apply Amsterdam/Madrid filter,
apply full matcher, show real match candidates.
"""
import requests, json, sys, os, html, re
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from matcher import score_job, flatten_matched

H = {"User-Agent": "Mozilla/5.0 Chrome/120.0",
     "Accept": "application/json"}

# =====================================================
# 20 API endpoints validated during the survey
# =====================================================
ENDPOINTS = {
    # Greenhouse
    "Adyen":       ("greenhouse", "adyen"),
    "Datadog":     ("greenhouse", "datadog"),
    "Mews":        ("greenhouse", "mewssystems"),
    "Samsara":     ("greenhouse", "samsara"),
    "Flexport":    ("greenhouse", "flexport"),
    "MessageBird": ("greenhouse", "bird"),
    "Stripe":      ("greenhouse", "stripe"),
    "Twilio":      ("greenhouse", "twilio"),
    "Databricks":  ("greenhouse", "databricks"),
    "Optiver":     ("greenhouse", "optiverus"),
    # Ashby
    "Mollie":      ("ashby", "mollie"),
    "Datasnipper": ("ashby", "datasnipper"),
    "Miro":        ("ashby", "miro"),
    # SmartRecruiters
    "Uber":        ("smartrecruiters", "uber"),
    "Picnic":      ("smartrecruiters", "picnic"),
    "ServiceNow":  ("smartrecruiters", "servicenow"),
    # Lever
    "Mendix":      ("lever", "mendix"),
    # Recruitee
    "Bunq":        ("recruitee", "bunq"),
    # Workday (POST)
    "Workday":     ("workday_cxs",
                    "https://workday.wd5.myworkdayjobs.com/wday/cxs/workday/Workday/jobs"),
}


def _strip_html(s):
    if not s: return ""
    s = html.unescape(s)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def fetch_greenhouse(slug):
    """Greenhouse - include BOTH location.name AND offices[].name.
    Some jobs are multi-office (primary elsewhere, but also open in Amsterdam)."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    r = requests.get(url, headers=H, timeout=20)
    r.raise_for_status()
    out = []
    for j in r.json().get("jobs", []):
        primary = ((j.get("location") or {}).get("name","") or "").strip()
        offices = [(o.get("name","") or "").strip()
                   for o in (j.get("offices") or [])]
        # Combine: primary first, then any offices not already in primary
        parts = [primary] if primary else []
        for off in offices:
            if off and off.lower() not in primary.lower():
                parts.append(off)
        location = "; ".join(p for p in parts if p)

        out.append({
            "title":       j.get("title","").strip(),
            "location":    location,
            "url":         j.get("absolute_url",""),
            "description": _strip_html(j.get("content","") or "")[:5000],
        })
    return out


def fetch_ashby(slug):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=false"
    r = requests.get(url, headers=H, timeout=20)
    r.raise_for_status()
    out = []
    for j in r.json().get("jobs", []):
        out.append({
            "title":       j.get("title","").strip(),
            "location":    j.get("locationName","").strip() or j.get("location","").strip(),
            "url":         j.get("jobUrl", j.get("applyUrl","")),
            "description": _strip_html(j.get("descriptionHtml") or j.get("description","") or "")[:5000],
        })
    return out


def fetch_smartrecruiters(slug):
    # need to page - grab everything
    all_jobs = []
    offset = 0
    while True:
        url = (f"https://api.smartrecruiters.com/v1/companies/{slug}/postings"
               f"?limit=100&offset={offset}")
        r = requests.get(url, headers=H, timeout=20)
        r.raise_for_status()
        d = r.json()
        content = d.get("content", [])
        if not content: break
        for j in content:
            loc = j.get("location") or {}
            city = loc.get("city","") or ""
            country = loc.get("country","") or ""
            location_str = ", ".join(x for x in (city, country) if x)
            all_jobs.append({
                "title":       j.get("name","").strip(),
                "location":    location_str,
                "url":         j.get("ref","") or j.get("applyUrl","") or
                               f"https://jobs.smartrecruiters.com/{slug}/{j.get('id','')}",
                "description": "",  # descrizione richiede seconda call
            })
        offset += len(content)
        if offset >= d.get("totalFound", 0): break
        if offset > 1000: break  # safety
    return all_jobs


def fetch_lever(slug):
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    r = requests.get(url, headers=H, timeout=20)
    r.raise_for_status()
    out = []
    for j in r.json():
        cats = j.get("categories", {})
        out.append({
            "title":       j.get("text","").strip(),
            "location":    cats.get("location","").strip(),
            "url":         j.get("hostedUrl",""),
            "description": _strip_html(j.get("descriptionPlain") or
                                       j.get("description","") or "")[:5000],
        })
    return out


def fetch_recruitee(slug):
    url = f"https://{slug}.recruitee.com/api/offers/"
    r = requests.get(url, headers=H, timeout=20)
    r.raise_for_status()
    out = []
    for j in r.json().get("offers", []):
        out.append({
            "title":       j.get("title","").strip(),
            "location":    j.get("location","").strip() or
                           j.get("city","").strip(),
            "url":         j.get("careers_url","") or j.get("careers_apply_url",""),
            "description": _strip_html(j.get("description","") or "")[:5000],
        })
    return out


def fetch_workday(url):
    # POST endpoint
    body = {"appliedFacets":{},"limit":20,"offset":0,"searchText":""}
    all_jobs = []
    offset = 0
    while True:
        body["offset"] = offset
        r = requests.post(url, json=body,
                          headers={**H, "Content-Type":"application/json"},
                          timeout=20)
        if r.status_code != 200: break
        d = r.json()
        posts = d.get("jobPostings", [])
        if not posts: break
        base = url.split("/wday/cxs/")[0]
        for j in posts:
            path = j.get("externalPath","")
            all_jobs.append({
                "title":       j.get("title","").strip(),
                "location":    j.get("locationsText","").strip() or
                               j.get("bulletFields",[""])[0].strip(),
                "url":         base + path if path else "",
                "description": "",
            })
        offset += len(posts)
        if offset >= d.get("total", 0): break
        if offset > 500: break
    return all_jobs


FETCHERS = {
    "greenhouse":     fetch_greenhouse,
    "ashby":          fetch_ashby,
    "smartrecruiters":fetch_smartrecruiters,
    "lever":          fetch_lever,
    "recruitee":      fetch_recruitee,
    "workday_cxs":    fetch_workday,
}


def fetch_company(company, kind, slug_or_url):
    try:
        jobs = FETCHERS[kind](slug_or_url)
        return company, jobs, None
    except Exception as e:
        return company, [], f"{type(e).__name__}: {str(e)[:80]}"


# =========================================
# RUN
# =========================================
print("Fetching from 19 APIs in parallel...\n")
results = {}
with ThreadPoolExecutor(max_workers=10) as ex:
    futures = {ex.submit(fetch_company, c, k, s): c
               for c, (k, s) in ENDPOINTS.items()}
    for fut in as_completed(futures):
        c, jobs, err = fut.result()
        results[c] = (jobs, err)

# =========================================
# STATS
# =========================================
print(f"{'COMPANY':<14}{'TOTAL':<8}{'AMS/MAD':<10}{'HIGH':<7}{'MED':<7}NOTES")
print("=" * 90)

grand_total = 0
grand_ams_mad = 0
grand_high = 0
grand_med = 0
high_matches = []
med_matches = []

for company, (jobs, err) in results.items():
    if err:
        print(f"{company:<14}{'ERR':<8}{'-':<10}{'-':<7}{'-':<7}{err}")
        continue
    total = len(jobs)
    grand_total += total

    ams_mad = 0
    high, med = 0, 0
    for j in jobs:
        # Score with full pipeline (location + exclusion + matcher)
        r = score_job(j["title"], j["location"], j["description"])
        if not r["passes_hard_filters"]:
            continue
        ams_mad += 1
        s = r["score"]
        if s >= 70:
            high += 1
            high_matches.append((company, j["title"], j["location"],
                                 s, j["url"], flatten_matched(r["matched"])))
        elif s >= 50:
            med += 1
            med_matches.append((company, j["title"], j["location"],
                                s, j["url"], flatten_matched(r["matched"])))

    grand_ams_mad += ams_mad
    grand_high += high
    grand_med += med
    print(f"{company:<14}{total:<8}{ams_mad:<10}{high:<7}{med:<7}")

print("=" * 90)
print(f"{'TOTAL':<14}{grand_total:<8}{grand_ams_mad:<10}{grand_high:<7}{grand_med:<7}")

print(f"\n>>> HIGH MATCHES (score >= 70): {len(high_matches)}")
for c, t, l, s, u, kw in high_matches[:15]:
    print(f"  [{s}] {c:<12} {t}  ({l})")
    print(f"       {u[:90]}")
    print(f"       {kw[:150]}")

print(f"\n>>> MEDIUM MATCHES (50-69): {len(med_matches)}")
for c, t, l, s, u, kw in med_matches[:10]:
    print(f"  [{s}] {c:<12} {t}  ({l})")
