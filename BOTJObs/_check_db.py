# -*- coding: utf-8 -*-
"""Diagnose DB state - which jobs are marked as first_seen on which day."""
import sqlite3
from datetime import date

DB = "data/jobs.db"
today = date.today().isoformat()

with sqlite3.connect(DB) as conn:
    conn.row_factory = sqlite3.Row

    # Total jobs in DB
    total = conn.execute("SELECT COUNT(*) as c FROM jobs").fetchone()["c"]
    print(f"Total jobs in DB:              {total}")

    # Jobs by day
    by_day = conn.execute("""
      SELECT DATE(first_seen) as day, COUNT(*) as c,
             SUM(CASE WHEN score >= 70 THEN 1 ELSE 0 END) as high,
             SUM(CASE WHEN score >= 50 AND score < 70 THEN 1 ELSE 0 END) as med
      FROM jobs GROUP BY DATE(first_seen) ORDER BY day DESC
    """).fetchall()
    print("\nJobs by first_seen day:")
    print(f"  {'DAY':<12} {'TOTAL':<8} {'HIGH':<6} {'MED':<6}")
    for r in by_day:
        print(f"  {r['day']:<12} {r['c']:<8} {r['high']:<6} {r['med']:<6}")

    # Jobs "first_seen" today (whatever score)
    today_jobs = conn.execute("""
      SELECT company, title, score FROM jobs
      WHERE first_seen LIKE ? ORDER BY score DESC
    """, (f"{today}%",)).fetchall()
    print(f"\nJobs first_seen TODAY ({today}): {len(today_jobs)}")
    for j in today_jobs:
        print(f"  [{j['score']}] {j['company']:<12} {j['title'][:60]}")

    # High/Med matches "still open" (regardless of when first seen)
    open_high = conn.execute("""
      SELECT company, title, location, score, first_seen FROM jobs
      WHERE score >= 70 ORDER BY score DESC LIMIT 15
    """).fetchall()
    print(f"\nAll HIGH matches in DB ({len(open_high)}):")
    for j in open_high:
        print(f"  [{j['score']}] {j['company']:<12} {j['title'][:50]:<50} seen: {j['first_seen'][:10]}")
