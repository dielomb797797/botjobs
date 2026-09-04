# -*- coding: utf-8 -*-
"""
UNIFIED SCRAPER - Runs all 25 company scrapers.
Phase 1: 19 API-based scrapers in parallel (fast, ~7s)
Phase 2: 6 Playwright scrapers in parallel (slower, ~30-90s)
Returns list of (company, jobs, err_or_None).
"""
import logging, importlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from _real_test import ENDPOINTS, FETCHERS

log = logging.getLogger(__name__)

PW_COMPANIES = [
    ("Revolut",   "revolut"),
    ("Backbase",  "backbase"),
    ("Atlassian", "atlassian"),
    ("Justeat",   "justeat"),
    ("Booking",   "booking"),
    ("Cisco",     "cisco"),
]


def _run_api(company, kind, slug_or_url):
    try:
        jobs = FETCHERS[kind](slug_or_url)
        return company, jobs, None
    except Exception as e:
        return company, [], f"{type(e).__name__}: {str(e)[:120]}"


def _run_pw(company, module):
    try:
        mod = importlib.import_module(f"scrapers.{module}")
        jobs = mod.fetch_jobs()
        return company, jobs, None
    except Exception as e:
        return company, [], f"{type(e).__name__}: {str(e)[:120]}"


def scan_all_companies():
    """Return list of (company, jobs, err). Deduplicate companies by name."""
    results = {}

    # Phase 1: APIs in parallel
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(_run_api, c, k, s): c for c, (k, s) in ENDPOINTS.items()}
        for fut in as_completed(futs):
            c, jobs, err = fut.result()
            results[c] = (jobs, err)

    # Phase 2: Playwright in parallel (limited concurrency to avoid CPU/RAM thrash)
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(_run_pw, c, m): c for c, m in PW_COMPANIES}
        for fut in as_completed(futs):
            c, jobs, err = fut.result()
            results[c] = (jobs, err)

    return [(c, j, e) for c, (j, e) in results.items()]
