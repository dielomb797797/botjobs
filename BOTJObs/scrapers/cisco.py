# -*- coding: utf-8 -*-
"""CISCO - Playwright DOM extraction. Phenom-powered."""
import logging
from scrapers.pw_base import run_dom_extraction

log = logging.getLogger(__name__)

# Cisco Phenom - search by keyword. Multiple searches to cover roles.
URLS = [
    "https://jobs.cisco.com/jobs/SearchJobs/?listFilterMode=1&21178=%5B37704%5D&21178_format=6020",  # Netherlands
    "https://jobs.cisco.com/jobs/SearchJobs/?listFilterMode=1&21178=%5B37792%5D&21178_format=6020",  # Spain
]
PATTERN = r"careers\.cisco\.com/global/en/job/|jobs\.cisco\.com/global/en/job/"


def fetch_jobs():
    all_jobs = []
    seen = set()
    for url in URLS:
        try:
            raw = run_dom_extraction(url, PATTERN, wait_ms=6000, scroll_times=4)
        except Exception as e:
            log.warning("Cisco %s failed: %s", url, e)
            continue
        loc_hint = "Netherlands" if "37704" in url else "Spain"
        for r in raw:
            u = r["url"]
            if u in seen: continue
            seen.add(u)
            title = r["title"].split("\n")[0].strip()
            if not title or len(title) < 3: continue
            ctx = r.get("context","")
            location = loc_hint
            for line in ctx.split("\n"):
                line = line.strip()
                if any(c in line.lower() for c in ["amsterdam","madrid","barcelona","netherlands","spain"]) and len(line) < 80:
                    location = line; break
            all_jobs.append({
                "title": title,
                "location": location,
                "url": u,
                "description": ctx[:500],
            })
    log.info("Cisco: fetched %d jobs", len(all_jobs))
    return all_jobs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    js = fetch_jobs()
    print(f"Total: {len(js)}")
    for j in js[:10]:
        print(f"- {j['title']} | {j['location']}")
