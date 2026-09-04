# -*- coding: utf-8 -*-
"""
DIAGNOSTIC - shows what the bot has been doing.
- Scan history (how many, when)
- ALL jobs seen today with score distribution
- Sample rejected jobs with reason (proof the matcher is working)
- Sample HIGH/MED matches still in DB

Run: python diagnostic.py
"""
import sqlite3, sys, os
from datetime import date, datetime, timedelta
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DB_PATH
from matcher import score_job
from unified_scraper import scan_all_companies

BLUE  = "\033[36m"
GREEN = "\033[32m"
YELLOW= "\033[33m"
RED   = "\033[31m"
GRAY  = "\033[90m"
BOLD  = "\033[1m"
END   = "\033[0m"

today = date.today().isoformat()

def hdr(s):
    print(f"\n{BLUE}{BOLD}{'='*70}\n{s}\n{'='*70}{END}")

# ============================================================
# 1. SCAN HISTORY
# ============================================================
hdr("1. RECENT SCAN HISTORY")
with sqlite3.connect(DB_PATH) as conn:
    conn.row_factory = sqlite3.Row
    runs = conn.execute("""
      SELECT run_id, started_at, finished_at, sites_ok, sites_fail,
             new_jobs, high_matches
      FROM run_log
      ORDER BY run_id DESC
      LIMIT 15
    """).fetchall()

    print(f"{'RUN#':<6}{'START (UTC)':<22}{'DURATION':<12}{'OK/FAIL':<10}{'NEW':<6}{'HIGH':<6}")
    for r in runs:
        try:
            s = datetime.fromisoformat(r["started_at"])
            f = datetime.fromisoformat(r["finished_at"]) if r["finished_at"] else None
            dur = f"{(f-s).total_seconds():.0f}s" if f else "?"
        except Exception:
            dur = "?"
        print(f"{r['run_id']:<6}{r['started_at']:<22}{dur:<12}"
              f"{r['sites_ok']}/{r['sites_fail']:<7}"
              f"{(r['new_jobs'] or 0):<6}{(r['high_matches'] or 0):<6}")

# ============================================================
# 2. DB SUMMARY BY DAY
# ============================================================
hdr("2. JOBS IN DB BY DAY (first_seen)")
with sqlite3.connect(DB_PATH) as conn:
    conn.row_factory = sqlite3.Row
    by_day = conn.execute("""
      SELECT DATE(first_seen) AS day,
             COUNT(*) AS total,
             SUM(CASE WHEN score >= 70 THEN 1 ELSE 0 END) AS high,
             SUM(CASE WHEN score >= 50 AND score < 70 THEN 1 ELSE 0 END) AS med,
             SUM(CASE WHEN score < 50 THEN 1 ELSE 0 END) AS low
      FROM jobs GROUP BY DATE(first_seen) ORDER BY day DESC LIMIT 10
    """).fetchall()
    print(f"{'DAY':<12}{'TOTAL':<8}{'HIGH':<8}{'MED':<8}{'LOW':<8}")
    for r in by_day:
        marker = " <-- TODAY" if r["day"] == today else ""
        print(f"{r['day']:<12}{r['total']:<8}{GREEN}{r['high']:<8}{END}{YELLOW}{r['med']:<8}{END}{GRAY}{r['low']:<8}{END}{marker}")

# ============================================================
# 3. RE-SCORE A LIVE SAMPLE (proof the matcher works)
# ============================================================
hdr("3. LIVE PROOF: fetch few companies now and show scoring")
print("Running a live scan on 3 companies (Mollie, Datadog, Miro)...")
print("(this shows exactly what the matcher does with real data)\n")

# We reuse unified_scraper's function but call only specific companies
from _real_test import ENDPOINTS, FETCHERS

sample = ["Mollie", "Datadog", "Miro"]
buckets = {"REJECTED_LOC":[], "REJECTED_SENIOR":[], "REJECTED_KEYWORD":[],
           "LOW":[], "MED":[], "HIGH":[]}

for company in sample:
    kind, slug = ENDPOINTS[company]
    try:
        jobs = FETCHERS[kind](slug)
    except Exception as e:
        print(f"{RED}{company}: fetch failed - {e}{END}")
        continue
    print(f"{BLUE}{company}: {len(jobs)} jobs downloaded{END}")

    for j in jobs:
        r = score_job(j.get("title",""), j.get("location",""), j.get("description",""))
        item = (company, j.get("title","")[:55], j.get("location","")[:35], r)
        if not r["passes_hard_filters"]:
            reason = r.get("reason","")
            excl   = r.get("excluded_by",[])
            if reason == "seniority_too_high":
                buckets["REJECTED_SENIOR"].append(item)
            elif reason == "location_not_in_target":
                buckets["REJECTED_LOC"].append(item)
            elif excl:
                buckets["REJECTED_KEYWORD"].append(item + (excl,))
            else:
                buckets["REJECTED_LOC"].append(item)
        else:
            s = r["score"]
            if s >= 70: buckets["HIGH"].append(item)
            elif s >= 50: buckets["MED"].append(item)
            else: buckets["LOW"].append(item)

def show(label, items, color, max_show=5, show_reason=False):
    print(f"\n{color}{BOLD}[{label}] {len(items)} jobs{END}")
    for it in items[:max_show]:
        company, title, loc = it[0], it[1], it[2]
        r = it[3]
        extra = ""
        if show_reason and len(it) > 4:
            extra = f"  reason: {it[4]}"
        score = r.get("score", "-")
        print(f"  {color}[{score}]{END} {company:<10} {title:<55} {GRAY}{loc}{END}{extra}")

show("HIGH (>=70) - would notify", buckets["HIGH"], GREEN, 10)
show("MED (50-69) - would notify", buckets["MED"], YELLOW, 5)
show("LOW (<50) - scored too low", buckets["LOW"], GRAY, 5)
show("REJECTED: Senior/Staff/Lead prefix", buckets["REJECTED_SENIOR"], RED, 5)
show("REJECTED: Wrong location (not Amsterdam/Madrid)", buckets["REJECTED_LOC"], RED, 5)
show("REJECTED: Exclusion keyword hit", buckets["REJECTED_KEYWORD"], RED, 5, show_reason=True)

# ============================================================
# 4. HEALTH SUMMARY
# ============================================================
hdr("4. HEALTH SUMMARY")
n_scans_today = sum(1 for r in runs if r["started_at"].startswith(today))
n_scans_24h = 0
now = datetime.utcnow()
for r in runs:
    try:
        st = datetime.fromisoformat(r["started_at"])
        if (now - st) < timedelta(hours=24):
            n_scans_24h += 1
    except Exception:
        pass

with sqlite3.connect(DB_PATH) as conn:
    total_all = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    total_high = conn.execute("SELECT COUNT(*) FROM jobs WHERE score >= 70").fetchone()[0]
    total_med = conn.execute("SELECT COUNT(*) FROM jobs WHERE score >= 50 AND score < 70").fetchone()[0]

print(f"  Scans today:       {n_scans_today}")
print(f"  Scans last 24h:    {n_scans_24h}   (expected ~48 if 30-min cadence)")
print(f"  Total DB jobs:     {total_all}")
print(f"  All-time HIGH:     {total_high}")
print(f"  All-time MED:      {total_med}")

print(f"\n{GREEN}Done. If numbers above look sensible, the bot is working correctly.{END}")
