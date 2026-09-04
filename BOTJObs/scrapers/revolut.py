# -*- coding: utf-8 -*-
"""REVOLUT - Playwright DOM extraction. Job URLs: /careers/position/..."""
import logging
from scrapers.pw_base import run_dom_extraction, parse_card_text

log = logging.getLogger(__name__)

URL = "https://www.revolut.com/careers/"
PATTERN = r"revolut\.com/careers/position/"


def fetch_jobs():
    raw = run_dom_extraction(URL, PATTERN, wait_ms=5000, scroll_times=5)
    jobs = []
    for r in raw:
        title_full = r["title"]
        # Titles come as "Position Title\nOffice: City · City\nRemote: Country"
        parts = title_full.split("\n")
        title = parts[0].strip() if parts else title_full
        # location = concatenate office + remote lines
        loc_lines = [p.strip() for p in parts[1:] if p.strip()]
        location = " | ".join(loc_lines)[:200]
        jobs.append({
            "title": title,
            "location": location,
            "url": r["url"],
            "description": "",
        })
    log.info("Revolut: fetched %d jobs", len(jobs))
    return jobs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    js = fetch_jobs()
    print(f"Total: {len(js)}")
    for j in js[:5]:
        print(f"- {j['title']} | {j['location']}")
