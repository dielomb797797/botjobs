# -*- coding: utf-8 -*-
"""BOOKING - Playwright API interception. Real endpoint: jobs.booking.com/api/jobs"""
import logging
import asyncio
from scrapers.pw_base import run_api_intercept

log = logging.getLogger(__name__)

URL = "https://jobs.booking.com/booking/jobs?page=1&pageSize=100"
API_PATTERN = r"jobs\.booking\.com/api/jobs\?"


def fetch_jobs():
    captured = run_api_intercept(URL, API_PATTERN, wait_ms=8000)
    jobs = []
    seen_ids = set()
    for c in captured:
        data = c.get("data")
        if not isinstance(data, dict): continue
        # Booking JibeApply returns 'jobs': [...]  or 'results': [...]
        for key in ("jobs","results","data","items"):
            arr = data.get(key)
            if isinstance(arr, list) and arr:
                for j in arr:
                    if not isinstance(j, dict): continue
                    jid = j.get("id") or j.get("jobId") or j.get("req_id")
                    if jid in seen_ids: continue
                    seen_ids.add(jid)
                    title = (j.get("title") or j.get("name") or j.get("jobTitle")
                             or "").strip()
                    # locations can be an array
                    loc_val = j.get("location") or j.get("city")
                    if isinstance(loc_val, list):
                        loc_val = ", ".join(str(x) for x in loc_val)
                    elif isinstance(loc_val, dict):
                        loc_val = loc_val.get("city","") or loc_val.get("name","")
                    location = str(loc_val or "").strip()
                    juri = j.get("applyUrl") or j.get("url") or ""
                    if not juri and jid:
                        juri = f"https://jobs.booking.com/booking/job/{jid}"
                    desc = (j.get("description","") or "")[:5000]
                    jobs.append({
                        "title": title,
                        "location": location,
                        "url": juri,
                        "description": desc,
                    })
                break  # found the array, stop looking
    log.info("Booking: fetched %d jobs", len(jobs))
    return jobs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    js = fetch_jobs()
    print(f"Total: {len(js)}")
    for j in js[:10]:
        print(f"- {j['title']} | {j['location']}")
