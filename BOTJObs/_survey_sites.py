# -*- coding: utf-8 -*-
"""
Survey all 26 target sites: identify their ATS platform and test API access.
Output: table showing (company, platform, api_endpoint, jobs_count, sample_job)
"""
import requests
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

SITES = [
    ("Mollie",      "https://jobs.mollie.com/"),
    ("Revolut",     "https://www.revolut.com/careers/"),
    ("Uber",        "https://jobs.uber.com/en/"),
    ("Adyen",       "https://careers.adyen.com/vacancies"),
    ("Backbase",    "https://www.backbase.com/careers/jobs"),
    ("Atlassian",   "https://www.atlassian.com/company/careers/all-jobs"),
    ("Datadog",     "https://careers.datadoghq.com/all-jobs/"),
    ("Mews",        "https://www.mews.com/en/careers"),
    ("Samsara",     "https://www.samsara.com/uk/company/careers"),
    ("Flexport",    "https://www.flexport.com/careers/jobs/"),
    ("Optiver",     "https://www.optiver.com/join-us/jobs/"),
    ("Datasnipper", "https://careers.datasnipper.com/job-listing"),
    ("MessageBird", "https://bird.com/careers"),
    ("Picnic",      "https://jobs.picnic.app/en/"),
    ("Bunq",        "https://careers.bunq.com/"),
    ("Justeat",     "https://careers.justeattakeaway.com/global/en"),
    ("Mendix",      "https://www.mendix.com/careers/"),
    ("Booking",     "https://careers.booking.com/"),
    ("Miro",        "https://miro.com/careers/open-positions/"),
    ("Stripe",      "https://stripe.com/jobs/search"),
    ("Twilio",      "https://jobs.twilio.com/careers"),
    ("Databricks",  "https://www.databricks.com/company/careers"),
    ("Salesforce",  "https://www.salesforce.com/company/careers/jobs/"),
    ("ServiceNow",  "https://careers.servicenow.com/"),
    ("Workday",     "https://www.workday.com/en-us/company/careers.html"),
    ("Cisco",       "https://jobs.cisco.com/jobs/SearchJobs/"),
]

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ATS fingerprints found in HTML source
PLATFORMS = [
    ("Greenhouse",     r"boards(-api)?\.greenhouse\.io|boards\.greenhouse\.io/embed"),
    ("Lever",          r"jobs\.lever\.co|api\.lever\.co"),
    ("Ashby",          r"jobs\.ashbyhq\.com|api\.ashbyhq\.com"),
    ("SmartRecruiters",r"smartrecruiters\.com|api\.smartrecruiters\.com"),
    ("Workday",        r"myworkdayjobs\.com|myworkday"),
    ("Workable",       r"apply\.workable\.com|workable\.com"),
    ("Recruitee",      r"recruitee\.com"),
    ("BambooHR",       r"bamboohr\.com"),
    ("Teamtailor",     r"teamtailor\.com"),
    ("Personio",       r"personio\.de|jobs\.personio\.de"),
    ("Eightfold",      r"eightfold\.ai|apply\.eightfold\.ai"),
    ("iCIMS",          r"icims\.com"),
    ("Taleo",          r"taleo\.net"),
    ("SuccessFactors", r"successfactors\.com|sapsf\.com"),
    ("Phenom",         r"phenompeople\.com|phenom\.com"),
    ("Jobvite",        r"jobvite\.com"),
    ("Rippling",       r"ats\.rippling\.com"),
    ("Framer",         r"framer(usercontent)?\.com|framer\.website"),
    ("Next.js",        r"__NEXT_DATA__|_next/static"),
]

# Known API endpoints by company (populated as I find them)
KNOWN_APIS = {
    # will populate for each ATS as detected
}


def detect_platform(html: str):
    hits = []
    for name, pattern in PLATFORMS:
        if re.search(pattern, html, re.IGNORECASE):
            hits.append(name)
    return hits


def try_api_endpoint(company_slug: str, platform: str):
    """Try platform-specific public API endpoint."""
    slug_variants = [company_slug.lower(),
                     company_slug.lower().replace(" ", ""),
                     company_slug.lower().replace(" ", "-")]

    if platform == "Greenhouse":
        for s in slug_variants:
            url = f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs"
            try:
                r = requests.get(url, headers=HEADERS, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    return url, len(data.get("jobs", []))
            except Exception:
                pass
    elif platform == "Lever":
        for s in slug_variants:
            url = f"https://api.lever.co/v0/postings/{s}"
            try:
                r = requests.get(url, headers=HEADERS, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    return url, len(data) if isinstance(data, list) else 0
            except Exception:
                pass
    elif platform == "SmartRecruiters":
        for s in slug_variants:
            url = f"https://api.smartrecruiters.com/v1/companies/{s}/postings"
            try:
                r = requests.get(url, headers=HEADERS, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    return url, data.get("totalFound", 0)
            except Exception:
                pass
    elif platform == "Ashby":
        for s in slug_variants:
            url = f"https://api.ashbyhq.com/posting-api/job-board/{s}"
            try:
                r = requests.get(url, headers=HEADERS, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    return url, len(data.get("jobs", []))
            except Exception:
                pass
    elif platform == "Recruitee":
        for s in slug_variants:
            url = f"https://{s}.recruitee.com/api/offers/"
            try:
                r = requests.get(url, headers=HEADERS, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    return url, len(data.get("offers", []))
            except Exception:
                pass
    elif platform == "Teamtailor":
        for s in slug_variants:
            url = f"https://api.teamtailor.com/v1/jobs?filter[company]={s}"
            try:
                r = requests.get(url,
                    headers={**HEADERS, "X-Api-Version": "20210218"}, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    return url, len(data.get("data", []))
            except Exception:
                pass
    return None, None


def probe(entry):
    company, url = entry
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        status = r.status_code
        html = r.text
        size = len(html)
    except Exception as e:
        return {"company": company, "url": url,
                "status": f"ERR:{type(e).__name__}",
                "size": 0, "platforms": [], "api": None, "count": None}

    platforms = detect_platform(html)

    # Try APIs for known ATS
    api_url, count = None, None
    for p in platforms:
        api_url, count = try_api_endpoint(company, p)
        if api_url:
            break

    return {
        "company": company,
        "url": url,
        "status": status,
        "size": size,
        "platforms": platforms,
        "api": api_url,
        "count": count,
    }


results = []
with ThreadPoolExecutor(max_workers=6) as ex:
    futures = {ex.submit(probe, s): s for s in SITES}
    for fut in as_completed(futures):
        results.append(fut.result())

# Preserve original order
order = {c: i for i, (c, _) in enumerate(SITES)}
results.sort(key=lambda r: order[r["company"]])

print(f"\n{'AZIENDA':<13}{'HTTP':<7}{'PLATFORMS':<40}{'API JOBS':<12}")
print("=" * 105)
for r in results:
    plat = ", ".join(r["platforms"][:2]) if r["platforms"] else "-"
    api_info = ""
    if r["api"]:
        api_info = f"OK count={r['count']}"
    elif r["platforms"]:
        api_info = "no-api"
    else:
        api_info = "?"
    print(f"{r['company']:<13}{str(r['status']):<7}{plat[:38]:<40}{api_info:<12}")

# Summary
api_ok = sum(1 for r in results if r["api"])
plat_detected = sum(1 for r in results if r["platforms"])
print(f"\nAPI available: {api_ok}/{len(results)}   Platform detected: {plat_detected}/{len(results)}")

# Save detailed results
with open("_survey_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)
print("Details saved to _survey_results.json")
