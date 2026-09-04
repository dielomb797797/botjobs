# -*- coding: utf-8 -*-
"""Check recent matches (last 48h) - see what was found while notifications were off."""
import sys, os, sqlite3
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DB_PATH

# ANSI colors for terminal
GREEN="\033[32m"; YELLOW="\033[33m"; CYAN="\033[36m"; BOLD="\033[1m"; GRAY="\033[90m"; END="\033[0m"

# We use UTC because first_seen is stored UTC
now_utc = datetime.now(timezone.utc)
two_days_ago = (now_utc - timedelta(hours=48)).isoformat(timespec="seconds")

with sqlite3.connect(DB_PATH) as conn:
    conn.row_factory = sqlite3.Row

    # Recent scan history
    print(f"{CYAN}{BOLD}=== SCAN HISTORY (last 20) ==={END}")
    runs = conn.execute("""
        SELECT run_id, started_at, sites_ok, sites_fail, new_jobs, high_matches
        FROM run_log ORDER BY run_id DESC LIMIT 20
    """).fetchall()
    print(f"{'RUN':<6}{'STARTED (UTC)':<22}{'OK/FAIL':<10}{'NEW':<6}{'HIGH':<6}")
    for r in runs:
        marker = f"  {GREEN}<-- new{END}" if r["new_jobs"] and r["new_jobs"] > 0 else ""
        print(f"{r['run_id']:<6}{r['started_at']:<22}{r['sites_ok']}/{r['sites_fail']:<7}"
              f"{(r['new_jobs'] or 0):<6}{(r['high_matches'] or 0):<6}{marker}")

    # All jobs first_seen in last 48h
    print(f"\n{CYAN}{BOLD}=== NEW JOBS FOUND IN LAST 48h ==={END}")
    print(f"(threshold: first_seen >= {two_days_ago})\n")

    recent = conn.execute("""
        SELECT company, title, location, url, score, matched_kw, first_seen, notified_at
        FROM jobs
        WHERE first_seen >= ?
        ORDER BY score DESC, first_seen DESC
    """, (two_days_ago,)).fetchall()

    high = [r for r in recent if r["score"] >= 70]
    med  = [r for r in recent if 50 <= r["score"] < 70]
    low  = [r for r in recent if r["score"] < 50]

    print(f"{GREEN}{BOLD}HIGH matches (>=70): {len(high)}{END}")
    for r in high:
        notif = "✓ notified" if r["notified_at"] else "NOT notified"
        print(f"  {GREEN}[{r['score']}]{END} {r['company']:<12} {r['title'][:60]}")
        print(f"       {GRAY}loc:{END} {r['location'][:70]}")
        print(f"       {GRAY}seen:{END} {r['first_seen']}  |  {notif}")
        print(f"       {GRAY}url:{END} {r['url'][:100]}")
        print()

    print(f"{YELLOW}{BOLD}MEDIUM matches (50-69): {len(med)}{END}")
    for r in med:
        notif = "✓ notified" if r["notified_at"] else "NOT notified"
        print(f"  {YELLOW}[{r['score']}]{END} {r['company']:<12} {r['title'][:60]}  ({r['location'][:35]})")
        print(f"       {GRAY}seen:{END} {r['first_seen']}  |  {notif}")

    print(f"\n{GRAY}Below-threshold (<50): {len(low)} — filtered out{END}")

    # SUMMARY
    print(f"\n{CYAN}{BOLD}=== SUMMARY ==={END}")
    print(f"  Total new jobs seen last 48h: {len(recent)}")
    print(f"  {GREEN}HIGH matches:{END}   {len(high)}")
    print(f"  {YELLOW}MEDIUM matches:{END} {len(med)}")
    print(f"  {GRAY}Below threshold:{END} {len(low)}")
