# -*- coding: utf-8 -*-
"""FULL TEST: all 26 companies (20 API + 6 Playwright).
Runs API scrapers in parallel, Playwright ones sequential (to avoid CPU thrash).
"""
import sys, os, time, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import API-based fetchers from _real_test.py logic
from _real_test import ENDPOINTS, FETCHERS, fetch_company
from concurrent.futures import ThreadPoolExecutor, as_completed
from matcher import score_job, flatten_matched

PW_COMPANIES = ["Revolut","Backbase","Atlassian","Justeat","Booking","Cisco"]


def run_pw_scraper(name):
    """Run one Playwright scraper. Returns (name, jobs, error)."""
    try:
        mod = importlib.import_module(f"scrapers.{name.lower()}")
        jobs = mod.fetch_jobs()
        return name, jobs, None
    except Exception as e:
        return name, [], f"{type(e).__name__}: {str(e)[:120]}"


# ========== PHASE 1: API scrapers (fast, in parallel) ==========
print("PHASE 1: fetching 19 API endpoints in parallel...")
t0 = time.time()
api_results = {}
with ThreadPoolExecutor(max_workers=10) as ex:
    futs = {ex.submit(fetch_company, c, k, s): c for c, (k, s) in ENDPOINTS.items()}
    for fut in as_completed(futs):
        c, jobs, err = fut.result()
        api_results[c] = (jobs, err)
api_elapsed = round(time.time() - t0, 1)
print(f"  Phase 1 done in {api_elapsed}s\n")

# ========== PHASE 2: Playwright scrapers (parallel with ThreadPool) ==========
print("PHASE 2: fetching 6 Playwright sites in parallel...")
t1 = time.time()
pw_results = {}
with ThreadPoolExecutor(max_workers=3) as ex:
    futs = {ex.submit(run_pw_scraper, c): c for c in PW_COMPANIES}
    for fut in as_completed(futs):
        c, jobs, err = fut.result()
        pw_results[c] = (jobs, err)
pw_elapsed = round(time.time() - t1, 1)
print(f"  Phase 2 done in {pw_elapsed}s\n")

# ========== SCORING & REPORT ==========
print(f"{'COMPANY':<14}{'SRC':<5}{'TOTAL':<8}{'AMS/MAD':<10}{'HIGH':<7}{'MED':<7}NOTES")
print("=" * 105)

all_results = {}
for c, v in api_results.items(): all_results[c] = ("API", v)
for c, v in pw_results.items():  all_results[c] = ("PW",  v)

grand_total = 0; grand_ams_mad = 0; grand_high = 0; grand_med = 0
high_matches = []; med_matches = []
failures = []

# Fixed order
ORDER = list(ENDPOINTS.keys()) + PW_COMPANIES
for company in ORDER:
    if company not in all_results: continue
    src, (jobs, err) = all_results[company]
    if err:
        print(f"{company:<14}{src:<5}{'ERR':<8}{'-':<10}{'-':<7}{'-':<7}{err[:60]}")
        failures.append((company, err))
        continue

    total = len(jobs)
    grand_total += total
    ams_mad, high, med = 0, 0, 0
    for j in jobs:
        r = score_job(j.get("title",""), j.get("location",""), j.get("description",""))
        if not r["passes_hard_filters"]: continue
        ams_mad += 1
        s = r["score"]
        if s >= 70:
            high += 1
            high_matches.append((company, j["title"], j.get("location",""), s,
                                 j.get("url",""), flatten_matched(r["matched"])))
        elif s >= 50:
            med += 1
            med_matches.append((company, j["title"], j.get("location",""), s,
                                j.get("url",""), flatten_matched(r["matched"])))
    grand_ams_mad += ams_mad
    grand_high += high
    grand_med += med
    print(f"{company:<14}{src:<5}{total:<8}{ams_mad:<10}{high:<7}{med:<7}")

print("=" * 105)
print(f"{'TOTAL 26':<14}{'':<5}{grand_total:<8}{grand_ams_mad:<10}{grand_high:<7}{grand_med:<7}")
print(f"\nTIMING: API {api_elapsed}s + Playwright {pw_elapsed}s = TOTAL {round(api_elapsed+pw_elapsed,1)}s")
print(f"COVERAGE: {len(all_results) - len(failures)}/{len(all_results)} companies OK ({len(failures)} failed)")

print(f"\n>>> HIGH MATCHES (score >= 70): {len(high_matches)}")
# Sort by score desc
for c, t, l, s, u, kw in sorted(high_matches, key=lambda x: -x[3])[:20]:
    print(f"  [{s}] {c:<12} {t[:70]}")
    print(f"       loc: {l[:80]}")
    print(f"       url: {u[:100]}")

print(f"\n>>> MEDIUM MATCHES (50-69): {len(med_matches)}")
for c, t, l, s, u, kw in sorted(med_matches, key=lambda x: -x[3])[:8]:
    print(f"  [{s}] {c:<12} {t[:70]}  ({l[:40]})")

if failures:
    print(f"\n>>> FAILURES:")
    for c, e in failures:
        print(f"  {c}: {e[:120]}")
