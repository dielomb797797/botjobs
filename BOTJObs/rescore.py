# -*- coding: utf-8 -*-
"""
RESCORE - Re-fetches all sites and updates the score of jobs already in the DB
with the current config's criteria.

Use case: config changed (new titles, new exclusions) - existing jobs need
re-scoring so they show up correctly in reports.

Run: python rescore.py
"""
import os, sys, sqlite3, logging
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DB_PATH, SCORE_THRESHOLD_HIGH, SCORE_THRESHOLD_MEDIUM
from matcher import score_job, flatten_matched
from unified_scraper import scan_all_companies
import storage

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("rescore")


def rescore_all():
    log.info("=" * 60)
    log.info("RESCORE STARTED - fetching all 25 companies to re-evaluate scores")
    log.info("=" * 60)

    storage.init_db()
    results = scan_all_companies()

    total_fetched = 0
    updated_up   = 0   # score raised
    updated_down = 0   # score lowered
    inserted     = 0   # truly new
    unchanged    = 0

    now = datetime.utcnow().isoformat(timespec="seconds")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        for company, jobs, err in results:
            if err:
                log.warning("[FAIL] %s: %s", company, err)
                continue
            log.info("[OK] %s: %d jobs", company, len(jobs))
            for j in jobs:
                total_fetched += 1
                title = j.get("title","")
                location = j.get("location","")
                desc = j.get("description","")
                url = j.get("url","")
                r = score_job(title, location, desc)
                if not r["passes_hard_filters"]:
                    continue   # not a match, skip
                score = r["score"]
                matched_kw = flatten_matched(r["matched"])
                job_id = storage.make_job_id(company, title, url)

                existing = conn.execute(
                    "SELECT score, first_seen FROM jobs WHERE job_id = ?",
                    (job_id,)).fetchone()

                if existing:
                    old_score = existing["score"]
                    if old_score != score:
                        conn.execute("""
                            UPDATE jobs SET score = ?, matched_kw = ?
                            WHERE job_id = ?
                        """, (score, matched_kw, job_id))
                        if score > old_score:
                            updated_up += 1
                            log.info("  UP  [%d -> %d] %s: %s",
                                     old_score, score, company, title[:60])
                        else:
                            updated_down += 1
                            log.info("  DN  [%d -> %d] %s: %s",
                                     old_score, score, company, title[:60])
                    else:
                        unchanged += 1
                else:
                    # Truly new job (not seen before at all)
                    conn.execute("""
                        INSERT INTO jobs (job_id, company, title, location, url,
                                          score, matched_kw, first_seen)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (job_id, company, title, location, url,
                          score, matched_kw, now))
                    inserted += 1
                    log.info("  NEW [%d] %s: %s", score, company, title[:60])

        conn.commit()

    log.info("=" * 60)
    log.info("RESCORE DONE")
    log.info("  Total jobs fetched: %d", total_fetched)
    log.info("  Score raised:       %d", updated_up)
    log.info("  Score lowered:      %d", updated_down)
    log.info("  Unchanged:          %d", unchanged)
    log.info("  Newly inserted:     %d", inserted)
    log.info("=" * 60)
    return updated_up, updated_down, inserted


if __name__ == "__main__":
    rescore_all()
