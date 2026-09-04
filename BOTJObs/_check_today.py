# -*- coding: utf-8 -*-
"""Stato di oggi: scan + nuovi job."""
import sys, os, sqlite3
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DB_PATH

GREEN="\033[32m"; YELLOW="\033[33m"; CYAN="\033[36m"; BOLD="\033[1m"; GRAY="\033[90m"; END="\033[0m"

today = date.today().isoformat()  # 2026-09-04

with sqlite3.connect(DB_PATH) as conn:
    conn.row_factory = sqlite3.Row

    # Scan di oggi
    print(f"{CYAN}{BOLD}=== SCAN DI OGGI ({today}) ==={END}")
    runs = conn.execute("""
        SELECT run_id, started_at, sites_ok, sites_fail, new_jobs, high_matches
        FROM run_log
        WHERE started_at LIKE ?
        ORDER BY run_id DESC
    """, (f"{today}%",)).fetchall()

    print(f"{'RUN':<6}{'ORA (UTC)':<22}{'OK/FAIL':<10}{'NEW':<6}{'HIGH':<6}")
    total_scans = len(runs)
    total_new = 0
    for r in runs:
        marker = f"  {GREEN}<-- new{END}" if r["new_jobs"] and r["new_jobs"] > 0 else ""
        print(f"{r['run_id']:<6}{r['started_at']:<22}{r['sites_ok']}/{r['sites_fail']:<7}"
              f"{(r['new_jobs'] or 0):<6}{(r['high_matches'] or 0):<6}{marker}")
        total_new += r["new_jobs"] or 0
    print(f"\n  Total scans today: {total_scans}")
    print(f"  Total new jobs across today's scans: {total_new}")

    # New jobs first-seen today
    print(f"\n{CYAN}{BOLD}=== JOB NUOVI SCOPERTI OGGI ==={END}")
    new_today = conn.execute("""
        SELECT company, title, location, url, score, matched_kw, first_seen
        FROM jobs
        WHERE first_seen LIKE ?
        ORDER BY score DESC
    """, (f"{today}%",)).fetchall()

    high = [j for j in new_today if j["score"] >= 70]
    med  = [j for j in new_today if 50 <= j["score"] < 70]
    low  = [j for j in new_today if j["score"] < 50]

    if high:
        print(f"\n{GREEN}{BOLD}HIGH matches (>=70): {len(high)}{END}")
        for j in high:
            print(f"  {GREEN}[{j['score']}]{END} {j['company']:<12} {j['title'][:65]}")
            print(f"       {GRAY}loc:{END} {j['location'][:70]}")
            print(f"       {GRAY}url:{END} {j['url'][:100]}")
            print(f"       {GRAY}seen:{END} {j['first_seen']}\n")
    else:
        print(f"\n{GRAY}HIGH matches (>=70): 0{END}")

    if med:
        print(f"\n{YELLOW}{BOLD}MEDIUM matches (50-69): {len(med)}{END}")
        for j in med:
            print(f"  {YELLOW}[{j['score']}]{END} {j['company']:<12} {j['title'][:65]}  ({j['location'][:35]})")
            print(f"       {GRAY}url:{END} {j['url'][:100]}")
    else:
        print(f"\n{GRAY}MEDIUM matches (50-69): 0{END}")

    if low:
        print(f"\n{GRAY}Below-threshold new today (<50): {len(low)}{END}")
        for j in low[:10]:
            print(f"  {GRAY}[{j['score']}] {j['company']:<12} {j['title'][:65]}  ({j['location'][:35]}){END}")

    print(f"\n{CYAN}{BOLD}=== SUMMARY OGGI ==={END}")
    print(f"  Total new: {len(new_today)}  |  HIGH: {len(high)}  MED: {len(med)}  LOW: {len(low)}")
