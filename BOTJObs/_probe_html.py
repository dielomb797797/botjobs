# -*- coding: utf-8 -*-
"""
Deep HTML inspection for the 7 remaining companies.
Dump: platform hints, api endpoints, embedded JSON keys.
"""
import requests, re, json

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36"),
}

TARGETS = [
    ("Revolut",   "https://www.revolut.com/careers/"),
    ("Backbase",  "https://www.backbase.com/careers/jobs"),
    ("Atlassian", "https://www.atlassian.com/company/careers/all-jobs"),
    ("Optiver",   "https://www.optiver.com/join-us/jobs/"),
    ("Justeat",   "https://careers.justeattakeaway.com/global/en/search-results"),
    ("Booking",   "https://careers.booking.com/en/search-results"),
    ("Cisco",     "https://jobs.cisco.com/jobs/SearchJobs/"),
]

# Try alternate URLs if the main one is 403
ALT_URLS = {
    "Revolut":  ["https://jobs.eu.lever.co/revolut", "https://boards.greenhouse.io/revolut",
                 "https://www.linkedin.com/company/revolut/jobs"],
}

PATTERNS = [
    ("api-jobs",       r'(https?:\\?/\\?/[^\s"\'<>]+(?:api|graphql|search|jobs)[^\s"\'<>]{0,120})'),
    ("workday-tenant", r'([a-z0-9-]+\.wd[0-9]+\.myworkdayjobs\.com/[a-zA-Z0-9_/-]+)'),
    ("greenhouse",     r'(boards[^/"]*greenhouse\.io/[a-z0-9_-]+)'),
    ("lever",          r'(jobs\.lever\.co/[a-z0-9_-]+)'),
    ("ashby",          r'(jobs\.ashbyhq\.com/[a-z0-9_-]+)'),
    ("smartrecruiters",r'(smartrecruiters\.com/[a-zA-Z0-9_/-]+)'),
    ("icims",          r'([a-z0-9-]+\.icims\.com/[a-zA-Z0-9_/-]+)'),
    ("phenom",         r'([a-z0-9-]+\.phenompeople\.com|phenom[a-z]*\.com)'),
    ("eightfold",      r'([a-z0-9-]+\.eightfold\.ai)'),
    ("teamtailor",     r'(career\.[a-z0-9-]+\.com/api|teamtailor\.com)'),
]

for company, url in TARGETS:
    print(f"\n{'='*70}\n{company:<12}  {url}\n{'='*70}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        html = r.text
        print(f"HTTP {r.status_code} - size: {len(html)}")
        if r.status_code >= 400:
            print("  (blocked - trying alt URLs)")
            for alt in ALT_URLS.get(company, []):
                r2 = requests.get(alt, headers=HEADERS, timeout=10)
                print(f"  alt {alt}: HTTP {r2.status_code}")
        # collect matches
        for name, pat in PATTERNS:
            hits = set(re.findall(pat, html, re.IGNORECASE))
            if hits:
                print(f"  [{name}] {len(hits)} hits:")
                for h in list(hits)[:6]:
                    print(f"     - {h[:110]}")
    except Exception as e:
        print(f"ERR: {e}")
