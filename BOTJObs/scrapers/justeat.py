# -*- coding: utf-8 -*-
"""JUST EAT TAKEAWAY - Playwright DOM extraction. Phenom-powered."""
import logging
from scrapers.pw_base import run_dom_extraction

log = logging.getLogger(__name__)

# Load broad search - Phenom filters by keyword in URL. Multiple searches to cover roles.
URLS = [
    "https://careers.justeattakeaway.com/global/en/search-results?keywords=engineer",
    "https://careers.justeattakeaway.com/global/en/search-results?keywords=solutions",
    "https://careers.justeattakeaway.com/global/en/search-results?keywords=integration",
    "https://careers.justeattakeaway.com/global/en/search-results?keywords=technical",
]
PATTERN = r"careers\.justeattakeaway\.com/global/en/job/"


def fetch_jobs():
    all_jobs = []
    seen = set()
    for url in URLS:
        try:
            raw = run_dom_extraction(url, PATTERN, wait_ms=5000, scroll_times=4)
        except Exception as e:
            log.warning("Justeat %s failed: %s", url, e)
            continue
        for r in raw:
            u = r["url"]
            if u in seen: continue
            seen.add(u)
            title = r["title"].split("\n")[0].strip()
            if not title or len(title) < 3: continue
            # location: extract from context text
            ctx = r.get("context","")
            location = ""
            for line in ctx.split("\n"):
                line = line.strip()
                for city in ["Amsterdam","Madrid","Barcelona","Berlin","Netherlands",
                             "Spain","Germany","UK","London","Bristol"]:
                    if city.lower() in line.lower() and len(line) < 80:
                        location = line
                        break
                if location: break
            all_jobs.append({
                "title": title,
                "location": location,
                "url": u,
                "description": ctx[:500],
            })
    log.info("Justeat: fetched %d jobs", len(all_jobs))
    return all_jobs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    js = fetch_jobs()
    print(f"Total: {len(js)}")
    for j in js[:10]:
        print(f"- {j['title']} | {j['location']}")
