# -*- coding: utf-8 -*-
"""
Aggressive survey - brute force each company against every known ATS API.
For each company, try:
  Greenhouse: boards-api.greenhouse.io/v1/boards/{slug}/jobs
  Lever:      api.lever.co/v0/postings/{slug}
  Ashby:      api.ashbyhq.com/posting-api/job-board/{slug}
  SmartRecruiters: api.smartrecruiters.com/v1/companies/{slug}/postings
  Recruitee:  {slug}.recruitee.com/api/offers/
  Personio:   {slug}.jobs.personio.com/xml
"""
import requests, json
from concurrent.futures import ThreadPoolExecutor, as_completed

COMPANIES = [
    "Mollie", "Revolut", "Uber", "Adyen", "Backbase", "Atlassian", "Datadog",
    "Mews", "Samsara", "Flexport", "Optiver", "Datasnipper", "MessageBird",
    "Picnic", "Bunq", "Justeat", "Mendix", "Booking", "Miro", "Stripe",
    "Twilio", "Databricks", "Salesforce", "ServiceNow", "Workday", "Cisco",
]

# Extra slug hints (empirical)
SLUG_ALIASES = {
    "MessageBird": ["messagebird", "bird"],
    "Justeat":     ["justeat", "justeattakeaway", "just-eat-takeaway", "jet"],
    "Mendix":      ["mendix", "siemens"],
    "Databricks":  ["databricks"],
    "Salesforce":  ["salesforce"],
    "ServiceNow":  ["servicenow"],
    "Mollie":      ["mollie"],
    "Revolut":     ["revolut"],
    "Adyen":       ["adyen"],
    "Backbase":    ["backbase"],
    "Atlassian":   ["atlassian"],
    "Datadog":     ["datadog", "datadoghq"],
    "Mews":        ["mews", "mewssystems"],
    "Samsara":     ["samsara", "samsaranetworks"],
    "Flexport":    ["flexport"],
    "Optiver":     ["optiver"],
    "Datasnipper": ["datasnipper"],
    "Picnic":      ["picnic", "picnicsupermarket"],
    "Bunq":        ["bunq"],
    "Booking":     ["booking", "bookingcom", "booking-com"],
    "Miro":        ["miro", "realtimeboard"],
    "Stripe":      ["stripe"],
    "Twilio":      ["twilio"],
    "Workday":     ["workday"],
    "Cisco":       ["cisco"],
    "Uber":        ["uber"],
}

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

def _get(url, headers=None, timeout=8):
    try:
        h = dict(HEADERS)
        if headers: h.update(headers)
        r = requests.get(url, headers=h, timeout=timeout)
        return r.status_code, r
    except Exception as e:
        return None, str(e)

def try_greenhouse(slug):
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    code, r = _get(url)
    if code == 200:
        try:
            return url, len(r.json().get("jobs", []))
        except Exception: return None, None
    return None, None

def try_lever(slug):
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    code, r = _get(url)
    if code == 200:
        try:
            d = r.json()
            return url, (len(d) if isinstance(d, list) else 0)
        except Exception: return None, None
    return None, None

def try_ashby(slug):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    code, r = _get(url)
    if code == 200:
        try:
            return url, len(r.json().get("jobs", []))
        except Exception: return None, None
    return None, None

def try_smart(slug):
    url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=1"
    code, r = _get(url)
    if code == 200:
        try:
            return url.replace("&limit=1","").replace("?limit=1",""), r.json().get("totalFound", 0)
        except Exception: return None, None
    return None, None

def try_recruitee(slug):
    url = f"https://{slug}.recruitee.com/api/offers/"
    code, r = _get(url)
    if code == 200:
        try:
            return url, len(r.json().get("offers", []))
        except Exception: return None, None
    return None, None

def try_personio(slug):
    url = f"https://{slug}.jobs.personio.com/xml"
    code, r = _get(url)
    if code == 200 and b"<workzag-jobs>" in (r.content or b""):
        n = r.text.count("<position>")
        return url, n
    return None, None

def try_teamtailor(slug):
    url = f"https://career.{slug}.com/api/v1/careersite/jobs"
    code, r = _get(url)
    if code == 200:
        try:
            return url, len(r.json().get("data", []))
        except Exception: return None, None
    return None, None

# Known custom endpoints (sniffed manually from popular sites)
CUSTOM_ENDPOINTS = {
    "Booking":   "https://careers.booking.com/api/jobs",
    "Miro":      "https://miro.com/api/careers/positions/",
    "Stripe":    "https://api.stripe.com/careers/positions",  # unlikely
    "Uber":      "https://jobs.uber.com/graphql",  # graphql
    "Databricks":"https://databricks.com/company/careers/all-open-positions?format=json",
    "Salesforce":"https://salesforce.wd12.myworkdayjobs.com/wday/cxs/salesforce/External_Career_Site/jobs",
    "ServiceNow":"https://careers.servicenow.com/api/jobs",
    "Workday":   "https://workday.wd5.myworkdayjobs.com/wday/cxs/workday/Workday/jobs",
    "Adyen":     "https://careers.adyen.com/api/jobs",
    "Backbase":  "https://www.backbase.com/api/careers/jobs",
    "Atlassian": "https://www.atlassian.com/endpoint/careers/allroles?locations=Netherlands",
    "Datadog":   "https://careers.datadoghq.com/api/jobs/",
    "Optiver":   "https://www.optiver.com/wp-json/wp/v2/jobs?per_page=100",
    "Picnic":    "https://picnic.recruitee.com/api/offers/",
    "Bunq":      "https://api.bunq.com/careers/positions",
    "MessageBird":"https://bird.com/api/careers/jobs",
    "Mews":      "https://www.mews.com/api/careers/positions",
    "Justeat":   "https://careers.justeattakeaway.com/api/jobs",
    "Mendix":    "https://www.mendix.com/api/careers/positions",
    "Cisco":     "https://jobs.cisco.com/api/careers/positions",
    "Revolut":   "https://www.revolut.com/api/careers/positions",
    "Twilio":    "https://twilio.eightfold.ai/api/apply/v2/jobs?domain=twilio.com&start=0&num=10",
    "Samsara":   "https://api.smartrecruiters.com/v1/companies/samsara/postings?limit=1",
    "Flexport":  "https://boards-api.greenhouse.io/v1/boards/flexport/jobs",
    "Datasnipper":"https://api.ashbyhq.com/posting-api/job-board/datasnipper",
    "Mollie":    "https://jobs.mollie.com/api/jobs",  # unknown
}

def probe_company(company):
    slugs = SLUG_ALIASES.get(company, [company.lower()])
    found = []

    # Standard ATS attempts
    for slug in slugs:
        for name, fn in [
            ("Greenhouse", try_greenhouse),
            ("Lever",      try_lever),
            ("Ashby",      try_ashby),
            ("SmartRecruiters", try_smart),
            ("Recruitee",  try_recruitee),
            ("Personio",   try_personio),
            ("Teamtailor", try_teamtailor),
        ]:
            api_url, count = fn(slug)
            if api_url and count is not None and count > 0:
                found.append((name, slug, api_url, count))
                break  # got one, move to next platform

    # Custom endpoint attempt
    custom = CUSTOM_ENDPOINTS.get(company)
    if custom:
        code, r = _get(custom, timeout=10)
        if code == 200:
            try:
                if hasattr(r, "json"):
                    d = r.json()
                    # rough count
                    cnt = None
                    if isinstance(d, list): cnt = len(d)
                    elif isinstance(d, dict):
                        for k in ("jobs","postings","positions","results","data","items","offers"):
                            if isinstance(d.get(k), list):
                                cnt = len(d[k]); break
                    if cnt is None: cnt = "json-ok"
                    found.append(("Custom", "-", custom, cnt))
            except Exception:
                found.append(("Custom", "-", custom, "non-json-200"))
        elif code:
            found.append(("Custom-tried", "-", custom, f"HTTP{code}"))

    return company, found


results = {}
with ThreadPoolExecutor(max_workers=8) as ex:
    futures = {ex.submit(probe_company, c): c for c in COMPANIES}
    for fut in as_completed(futures):
        c, f = fut.result()
        results[c] = f

# Preserve order
print(f"\n{'AZIENDA':<14}{'PLATFORM':<18}{'SLUG':<20}{'JOBS':<10}ENDPOINT")
print("=" * 130)
solid, custom_ok, unknown = 0, 0, 0
for c in COMPANIES:
    hits = results[c]
    real_hits = [h for h in hits if isinstance(h[3], int) and h[3] > 0]
    if real_hits:
        for h in real_hits:
            plat, slug, url, count = h
            print(f"{c:<14}{plat:<18}{slug:<20}{count:<10}{url[:70]}")
            if plat == "Custom": custom_ok += 1
            else: solid += 1
    else:
        # Show attempts
        if hits:
            plat, slug, url, count = hits[0]
            print(f"{c:<14}{plat:<18}{'-':<20}{str(count):<10}{url[:70]}")
        else:
            print(f"{c:<14}{'?':<18}{'-':<20}{'-':<10}(no api found)")
        unknown += 1

print(f"\nSOLID ATS API: {solid}   Custom-endpoint OK: {custom_ok}   Unknown: {unknown}")

with open("_survey_aggressive.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)
