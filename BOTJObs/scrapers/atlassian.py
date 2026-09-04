# -*- coding: utf-8 -*-
"""ATLASSIAN - Playwright DOM extraction. Uses filters for Netherlands+Spain."""
import logging
from scrapers.pw_base import run_dom_extraction

log = logging.getLogger(__name__)

# Two searches - Netherlands + Spain
URLS = [
    "https://www.atlassian.com/company/careers/all-jobs?team=&location=Netherlands&search=",
    "https://www.atlassian.com/company/careers/all-jobs?team=&location=Spain&search=",
]
PATTERN = r"atlassian\.com/company/careers/details/"


def fetch_jobs():
    all_jobs = []
    seen = set()
    for url in URLS:
        try:
            raw = run_dom_extraction(url, PATTERN, wait_ms=6000, scroll_times=6)
        except Exception as e:
            log.warning("Atlassian %s failed: %s", url, e)
            continue
        # infer location from URL
        loc_hint = "Netherlands" if "Netherlands" in url else "Spain"
        for r in raw:
            u = r["url"]
            if u in seen: continue
            seen.add(u)
            title = r["title"].split("\n")[0].strip()
            if not title or len(title) < 3: continue
            all_jobs.append({
                "title": title,
                "location": loc_hint,
                "url": u,
                "description": r.get("context","")[:500],
            })
    log.info("Atlassian: fetched %d jobs", len(all_jobs))
    return all_jobs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    js = fetch_jobs()
    print(f"Total: {len(js)}")
    for j in js[:10]:
        print(f"- {j['title']} | {j['location']}")
