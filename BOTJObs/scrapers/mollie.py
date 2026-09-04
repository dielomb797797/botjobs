# -*- coding: utf-8 -*-
"""
MOLLIE careers scraper.
Mollie uses a career page at https://jobs.mollie.com/ - built on Greenhouse.
Board token: 'mollie' -> Greenhouse public API: https://boards-api.greenhouse.io/v1/boards/mollie/jobs
"""
import logging
from scrapers.base import http_get_json

log = logging.getLogger(__name__)

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/mollie/jobs?content=true"


def fetch_jobs() -> list[dict]:
    """Return list of job dicts: title, location, url, description."""
    data = http_get_json(GREENHOUSE_API)
    if not data or "jobs" not in data:
        log.warning("Mollie: no jobs returned from Greenhouse API")
        return []

    jobs = []
    for j in data.get("jobs", []):
        title       = j.get("title", "").strip()
        location    = (j.get("location") or {}).get("name", "").strip()
        url         = j.get("absolute_url", "")
        # 'content' is HTML - strip tags roughly
        raw_content = j.get("content", "") or ""
        # decode HTML entities and strip tags for keyword scan
        try:
            import html, re
            desc = html.unescape(raw_content)
            desc = re.sub(r"<[^>]+>", " ", desc)
            desc = re.sub(r"\s+", " ", desc).strip()
        except Exception:
            desc = raw_content

        jobs.append({
            "title":       title,
            "location":    location,
            "url":         url,
            "description": desc,
        })

    log.info("Mollie: fetched %d jobs", len(jobs))
    return jobs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    js = fetch_jobs()
    print(f"Total jobs: {len(js)}")
    for j in js[:5]:
        print(f"- {j['title']}  |  {j['location']}")
        print(f"  {j['url']}")
