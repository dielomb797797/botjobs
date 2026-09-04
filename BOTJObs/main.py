# -*- coding: utf-8 -*-
"""
MAIN - Job Monitor entry point (DIGEST MODE).

Modes:
    python main.py once     -> single silent scan (populate DB, no notifs)
    python main.py digest   -> generate today's digest report + send toast
    python main.py loop     -> continuous: scan every hour + digest at 19:00
    python main.py test     -> desktop notification test
"""
import sys, os, time, logging, importlib
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (SITES, CHECK_INTERVAL_MINUTES, SCORE_THRESHOLD_HIGH,
                    SCORE_THRESHOLD_MEDIUM, LOG_PATH,
                    DAILY_DIGEST_HOUR, DAILY_DIGEST_MINUTE,
                    INSTANT_NOTIFY_ENABLED, INSTANT_NOTIFY_MIN_SCORE,
                    INSTANT_NOTIFY_MAX_PER_SCAN)
import storage
from matcher import score_job, flatten_matched
from notifier import send_toast


# ==========================================================
# ALL 26 COMPANIES - unified registry
# ==========================================================
# (company, scraper_module_name) - all scrapers expose fetch_jobs()
ALL_SITES = [
    # API-based (fast)
    ("Mollie",      "mollie_api"),
    ("Adyen",       "adyen_gh"),
    ("Datadog",     "datadog_gh"),
    ("Mews",        "mews_gh"),
    ("Samsara",     "samsara_gh"),
    ("Flexport",    "flexport_gh"),
    ("MessageBird", "bird_gh"),
    ("Stripe",      "stripe_gh"),
    ("Twilio",      "twilio_gh"),
    ("Databricks",  "databricks_gh"),
    ("Optiver",     "optiver_gh"),
    ("Datasnipper", "datasnipper_ashby"),
    ("Miro",        "miro_ashby"),
    ("Uber",        "uber_smart"),
    ("Picnic",      "picnic_smart"),
    ("ServiceNow",  "servicenow_smart"),
    ("Mendix",      "mendix_lever"),
    ("Bunq",        "bunq_recruitee"),
    ("Workday",     "workday_cxs"),
    # Playwright-based (slower)
    ("Revolut",     "revolut"),
    ("Backbase",    "backbase"),
    ("Atlassian",   "atlassian"),
    ("Justeat",     "justeat"),
    ("Booking",     "booking"),
    ("Cisco",       "cisco"),
]


# ==========================================================
# LOGGING
# ==========================================================
def setup_logging():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

log = logging.getLogger("main")


# ==========================================================
# SILENT SCAN CYCLE
# ==========================================================
def run_silent_scan():
    """Fetch all sites, score, save to DB. NO notifications sent."""
    from unified_scraper import scan_all_companies
    log.info("=" * 60)
    log.info("SILENT SCAN START (%d sites)", len(ALL_SITES))
    log.info("=" * 60)

    storage.init_db()
    run_id = storage.start_run()
    sites_ok, sites_fail = 0, 0
    new_jobs, high, med = 0, 0, 0
    instant_sent = 0

    results = scan_all_companies()
    for company, jobs, err in results:
        if err:
            log.warning("  [FAIL] %s: %s", company, err)
            sites_fail += 1
            continue
        sites_ok += 1
        log.info("  [OK]   %s: %d jobs", company, len(jobs))
        for j in jobs:
            title = j.get("title","")
            location = j.get("location","")
            desc = j.get("description","")
            url = j.get("url","")
            r = score_job(title, location, desc)
            if not r["passes_hard_filters"]: continue
            score = r["score"]
            job_id = storage.make_job_id(company, title, url)
            if not storage.is_new_job(job_id): continue
            kw = flatten_matched(r["matched"])
            storage.save_job(job_id, company, title, location, url, score, kw)
            new_jobs += 1
            if score >= SCORE_THRESHOLD_HIGH: high += 1
            elif score >= SCORE_THRESHOLD_MEDIUM: med += 1

            # === INSTANT NOTIFICATION for new HIGH match ===
            if (INSTANT_NOTIFY_ENABLED
                and score >= INSTANT_NOTIFY_MIN_SCORE
                and instant_sent < INSTANT_NOTIFY_MAX_PER_SCAN):
                try:
                    toast_title = f"[{score}] {company} - {title[:60]}"
                    toast_msg   = f"{location} | {kw[:120]}"
                    send_toast(title=toast_title, message=toast_msg,
                               url=url, tag=f"instant-{job_id}")
                    storage.mark_notified(job_id)
                    instant_sent += 1
                    log.info("  --> INSTANT NOTIF [%d] %s: %s",
                             score, company, title[:60])
                except Exception as e:
                    log.warning("Instant toast failed: %s", e)

    if instant_sent >= INSTANT_NOTIFY_MAX_PER_SCAN:
        # There were more matches than the cap - notify user
        remaining = high - instant_sent
        if remaining > 0:
            try:
                send_toast(
                    title=f"+{remaining} more HIGH matches in this scan",
                    message="Cap reached. All matches visible in tonight's 19:00 report.",
                    tag=f"cap-{run_id}",
                )
            except Exception:
                pass

    storage.finish_run(run_id, sites_ok, sites_fail, new_jobs, high)
    log.info("SCAN DONE. sites_ok=%d sites_fail=%d new=%d high=%d med=%d instant=%d",
             sites_ok, sites_fail, new_jobs, high, med, instant_sent)
    return new_jobs, high, med


# ==========================================================
# LOOP MODE (scan + daily digest at 19:00)
# ==========================================================
def run_loop():
    """Runs continuously: silent scan every CHECK_INTERVAL_MINUTES,
    fires daily digest once per day at DAILY_DIGEST_HOUR:MINUTE."""
    log.info("LOOP MODE started. Scan every %d min. Digest at %02d:%02d local.",
             CHECK_INTERVAL_MINUTES, DAILY_DIGEST_HOUR, DAILY_DIGEST_MINUTE)
    last_digest_date = None

    while True:
        try:
            # 1. Silent scan
            new, high, med = run_silent_scan()
        except Exception as e:
            log.exception("Scan error: %s", e)

        # 2. Check digest trigger
        now = datetime.now()
        today = now.date()
        trigger_time = now.replace(hour=DAILY_DIGEST_HOUR,
                                   minute=DAILY_DIGEST_MINUTE,
                                   second=0, microsecond=0)
        if now >= trigger_time and last_digest_date != today:
            try:
                from digest import send_daily_digest
                path, n = send_daily_digest()
                log.info("DIGEST SENT: %d matches. Report: %s", n, path)
                last_digest_date = today
            except Exception as e:
                log.exception("Digest error: %s", e)

        # 3. Sleep until next scan
        log.info("Sleeping %d min...", CHECK_INTERVAL_MINUTES)
        time.sleep(CHECK_INTERVAL_MINUTES * 60)


# ==========================================================
# TEST
# ==========================================================
def run_test():
    from notifier import send_toast
    log.info("Test toast...")
    send_toast("JobMonitor test",
               "If you see this popup, desktop notification works.",
               "https://example.com", tag="test-main")


# ==========================================================
# ENTRY
# ==========================================================
if __name__ == "__main__":
    setup_logging()
    mode = sys.argv[1] if len(sys.argv) > 1 else "once"
    if   mode == "once":   run_silent_scan()
    elif mode == "loop":   run_loop()
    elif mode == "digest":
        from digest import send_daily_digest
        p, n = send_daily_digest()
        print(f"Digest: {n} matches. Report: {p}")
    elif mode == "test":   run_test()
    else:
        print("Usage: python main.py [once|loop|digest|test]")
        sys.exit(1)
