# -*- coding: utf-8 -*-
"""BACKBASE - Playwright DOM extraction."""
import logging
from scrapers.pw_base import run_dom_extraction

log = logging.getLogger(__name__)

URL = "https://www.backbase.com/careers/jobs"
# Backbase job URLs pattern - test both possibilities
PATTERN = r"backbase\.com/careers/jobs/[a-z0-9-]{5,}|backbase\.com/careers/[a-z0-9-]+-[a-z0-9-]+"


def fetch_jobs():
    raw = run_dom_extraction(URL, PATTERN, wait_ms=6000, scroll_times=5)
    jobs = []
    seen = set()
    for r in raw:
        url = r["url"]
        if url in seen: continue
        # Filter out nav/menu links
        title = r["title"].split("\n")[0].strip()
        if not title or len(title) < 3 or title.lower() in ("jobs","stories","locations","learn more"):
            continue
        seen.add(url)
        ctx = r.get("context","")
        # Try to extract location from context
        location = ""
        for line in ctx.split("\n"):
            line = line.strip()
            for city in ["Amsterdam","Atlanta","Toronto","London","Kraków","Cardiff",
                         "Boise","New York","Mexico","Dubai","Singapore",
                         "Netherlands","Spain","Madrid","Barcelona"]:
                if city.lower() in line.lower() and 3 < len(line) < 100:
                    location = line
                    break
            if location: break
        jobs.append({
            "title": title,
            "location": location,
            "url": url,
            "description": ctx[:500],
        })
    log.info("Backbase: fetched %d jobs", len(jobs))
    return jobs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    js = fetch_jobs()
    print(f"Total: {len(js)}")
    for j in js[:5]:
        print(f"- {j['title']} | {j['location']}")
